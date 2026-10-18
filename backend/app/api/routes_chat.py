import json
import logging
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.auth.dependencies import get_current_user, get_ws_user
from app.db.models import DocumentModel, MessageModel, ThreadModel
from app.db.session import async_session_maker, get_db
from app.graph.workflow import chat_graph
from app.parsers.factory import get_parser_for_file
from app.retrieval.hybrid_store import document_registry

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])

class ChatStreamRequest(BaseModel):
    thread_id: str
    message: str
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = 0.3
    n_turns: Optional[int] = None

async def ensure_documents_indexed(documents: List[DocumentModel]):
    """Ensure large documents are registered in the in-memory hybrid store."""
    for d in documents:
        if d.strategy == "TOOL_RETRIEVAL" and not document_registry.get(d.id):
            file_path = Path(d.storage_path)
            if file_path.exists():
                try:
                    parser = get_parser_for_file(d.filename)
                    parsed_doc = await parser.parse(file_path, d.filename)
                    document_registry.register(d.id, parsed_doc)
                except Exception as e:
                    logger.error(f"Error re-indexing document {d.filename}: {e}")

async def sse_event_generator(
    req: ChatStreamRequest,
    current_user: str
) -> AsyncGenerator[str, None]:
    """Generates Server-Sent Events (SSE) from the LangGraph execution stream."""
    async with async_session_maker() as db:
        # Load thread and attached documents
        stmt = (
            select(ThreadModel)
            .where(ThreadModel.id == req.thread_id, ThreadModel.user_id == current_user)
            .options(selectinload(ThreadModel.messages), selectinload(ThreadModel.documents))
        )
        result = await db.execute(stmt)
        thread = result.scalar_one_or_none()
        
        if not thread:
            yield f"event: error\ndata: {json.dumps({'error': 'Thread not found'})}\n\n"
            return

        # Ensure documents are indexed
        await ensure_documents_indexed(thread.documents)
        
        # Prepare document representations for state
        docs_for_state = []
        routing_telemetry = []
        for d in thread.documents:
            text_content = ""
            if d.strategy == "DIRECT_CONTEXT":
                file_path = Path(d.storage_path)
                if file_path.exists():
                    try:
                        parser = get_parser_for_file(d.filename)
                        parsed = await parser.parse(file_path, d.filename)
                        text_content = parsed.text_content
                    except Exception:
                        pass
                        
            docs_for_state.append({
                "doc_id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "size_bytes": d.size_bytes,
                "token_count_estimate": d.token_count_estimate,
                "strategy": d.strategy,
                "summary_or_toc": d.summary_or_toc,
                "text_content": text_content
            })
            routing_telemetry.append({
                "id": d.id,
                "filename": d.filename,
                "strategy": d.strategy,
                "tokens": d.token_count_estimate
            })

        # Send initial metadata events
        n_turns = req.n_turns or thread.n_turns or 5
        provider = req.provider or thread.provider or "gemini"
        model_name = req.model_name or thread.model_name or settings.DEFAULT_MODEL or "gemini-3.5-flash"
        
        yield f"event: session_info\ndata: {json.dumps({'thread_id': thread.id, 'provider': provider, 'model_name': model_name, 'n_turns': n_turns})}\n\n"
        yield f"event: document_routing\ndata: {json.dumps({'documents': routing_telemetry})}\n\n"

        # Reconstruct LangGraph message history from DB
        history_messages = []
        for m in thread.messages:
            if m.role == "user":
                history_messages.append(HumanMessage(content=m.content, id=m.id))
            elif m.role == "assistant":
                history_messages.append(AIMessage(content=m.content, id=m.id, tool_calls=m.tool_calls or []))

        # Add new user message
        user_msg_id = str(uuid.uuid4())
        new_human_msg = HumanMessage(content=req.message, id=user_msg_id)
        history_messages.append(new_human_msg)

        # Build initial graph state
        initial_state = {
            "messages": history_messages,
            "summary": thread.summary or "",
            "n_turns": n_turns,
            "documents": docs_for_state,
            "direct_context": "",
            "large_docs_manifest": "",
            "thread_id": thread.id,
            "user_id": current_user,
            "provider_config": {
                "provider": provider,
                "model_name": model_name,
                "api_key": req.api_key,
                "base_url": req.base_url,
                "temperature": req.temperature or 0.3,
            },
            "summary_updated": False,
        }

        config = {"configurable": {"thread_id": thread.id}}
        
        assistant_content_parts: List[str] = []
        executed_tool_calls: List[Dict[str, Any]] = []
        latest_summary = thread.summary or ""

        try:
            async for event in chat_graph.astream_events(initial_state, config=config, version="v2"):
                kind = event["event"]
                
                # Streaming tokens from LLM
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    delta = chunk.content
                    if delta:
                        # chunk.content can occasionally be a string or list
                        delta_str = delta if isinstance(delta, str) else str(delta)
                        assistant_content_parts.append(delta_str)
                        yield f"event: token\ndata: {json.dumps({'delta': delta_str})}\n\n"

                # Tool call initiated
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "tool")
                    tool_input = event["data"].get("input", {})
                    yield f"event: tool_start\ndata: {json.dumps({'tool': tool_name, 'input': tool_input})}\n\n"

                # Tool call finished
                elif kind == "on_tool_end":
                    tool_name = event.get("name", "tool")
                    tool_output = str(event["data"].get("output", ""))
                    executed_tool_calls.append({"tool": tool_name, "output_preview": tool_output[:300]})
                    yield f"event: tool_end\ndata: {json.dumps({'tool': tool_name, 'output_preview': tool_output[:300]})}\n\n"

                # State node completed (e.g. summarizer updated)
                elif kind == "on_chain_end":
                    node_name = event.get("name")
                    output = event["data"].get("output")
                    if isinstance(output, dict) and output.get("summary_updated"):
                        latest_summary = output.get("summary", latest_summary)
                        yield f"event: summary_updated\ndata: {json.dumps({'summary': latest_summary})}\n\n"

        except Exception as e:
            logger.error(f"Error during streaming: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            return

        full_assistant_reply = "".join(assistant_content_parts)
        
        # Save User Message to Database
        db_user_msg = MessageModel(
            id=user_msg_id,
            thread_id=thread.id,
            role="user",
            content=req.message,
            turn_index=len(thread.messages) + 1,
            is_summarized=False
        )
        db.add(db_user_msg)

        # Save Assistant Message to Database
        assistant_msg_id = str(uuid.uuid4())
        db_assistant_msg = MessageModel(
            id=assistant_msg_id,
            thread_id=thread.id,
            role="assistant",
            content=full_assistant_reply,
            tool_calls=executed_tool_calls if executed_tool_calls else None,
            turn_index=len(thread.messages) + 2,
            is_summarized=False
        )
        db.add(db_assistant_msg)

        # Update Thread summary and metadata
        thread.summary = latest_summary
        thread.provider = provider
        thread.model_name = model_name
        thread.n_turns = n_turns
        
        # Auto-generate title if this was the first turn
        if len(thread.messages) == 0 and req.message:
            short_title = req.message.strip().split("\n")[0][:40]
            thread.title = short_title

        await db.commit()

        yield f"event: done\ndata: {json.dumps({'status': 'completed', 'user_message_id': user_msg_id, 'assistant_message_id': assistant_msg_id})}\n\n"

@router.post("/api/chat/stream")
async def chat_stream_endpoint(
    req: ChatStreamRequest,
    current_user: str = Depends(get_current_user)
):
    """Stream conversation response token-by-token over Server-Sent Events (SSE)."""
    return StreamingResponse(
        sse_event_generator(req, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket endpoint supporting real-time chat with 'on_resume' reconnection.
    """
    await websocket.accept()
    
    # Authenticate via token query param
    try:
        current_user = await get_ws_user(token)
    except HTTPException:
        await websocket.send_json({"type": "error", "message": "Authentication failed"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            # Reconnection / resume handling
            if action == "resume":
                thread_id = data.get("thread_id")
                last_message_id = data.get("last_message_id")
                
                async with async_session_maker() as db:
                    stmt = (
                        select(ThreadModel)
                        .where(ThreadModel.id == thread_id, ThreadModel.user_id == current_user)
                        .options(selectinload(ThreadModel.messages))
                    )
                    res = await db.execute(stmt)
                    thread = res.scalar_one_or_none()
                    
                    if thread:
                        messages = thread.messages
                        if last_message_id:
                            # Replay only messages after last_message_id
                            found = False
                            replay_msgs = []
                            for m in messages:
                                if found:
                                    replay_msgs.append(m)
                                elif m.id == last_message_id:
                                    found = True
                        else:
                            replay_msgs = messages
                            
                        await websocket.send_json({
                            "type": "resumed",
                            "thread_id": thread_id,
                            "summary": thread.summary,
                            "messages": [
                                {
                                    "id": m.id,
                                    "role": m.role,
                                    "content": m.content,
                                    "tool_calls": m.tool_calls,
                                    "created_at": m.created_at.isoformat()
                                }
                                for m in replay_msgs
                            ]
                        })

            # Sending new chat message
            elif action == "chat":
                req = ChatStreamRequest(
                    thread_id=data["thread_id"],
                    message=data["message"],
                    provider=data.get("provider"),
                    model_name=data.get("model_name"),
                    api_key=data.get("api_key"),
                    n_turns=data.get("n_turns")
                )
                
                # Stream events over WS
                async for sse_chunk in sse_event_generator(req, current_user):
                    # Parse SSE lines: 'event: <e>\ndata: <d>\n\n'
                    lines = sse_chunk.strip().split("\n")
                    ev_type = "message"
                    ev_data = {}
                    for line in lines:
                        if line.startswith("event: "):
                            ev_type = line[len("event: "):].strip()
                        elif line.startswith("data: "):
                            try:
                                ev_data = json.loads(line[len("data: "):].strip())
                            except Exception:
                                ev_data = {"raw": line[len("data: "):].strip()}
                    
                    await websocket.send_json({"type": ev_type, "payload": ev_data})

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for user {current_user}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
