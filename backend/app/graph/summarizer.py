import logging
from typing import Dict, List, Tuple
from langchain_core.messages import AnyMessage, HumanMessage, RemoveMessage, SystemMessage
from app.core.llm_factory import get_chat_model
from app.graph.state import ChatState

logger = logging.getLogger(__name__)

async def condense_older_turns(state: ChatState) -> Tuple[str, List[RemoveMessage]]:
    """
    Condense messages older than the last N conversational turns (2*N messages)
    into an updated rolling summary, and return RemoveMessages to prune them from state.
    """
    messages = state.get("messages", [])
    n_turns = state.get("n_turns", 5)
    max_raw_messages = n_turns * 2  # Each turn = 1 User + 1 Assistant
    
    if len(messages) <= max_raw_messages:
        return state.get("summary", ""), []
    
    # Split into older messages (to summarize) and recent messages (to preserve in full)
    older_messages = messages[:-max_raw_messages]
    
    # Format the transcript of older messages
    transcript_lines = []
    for m in older_messages:
        role = getattr(m, "type", "message")
        content = getattr(m, "content", "")
        if role in ["human", "user"]:
            transcript_lines.append(f"User: {content}")
        elif role in ["ai", "assistant"]:
            transcript_lines.append(f"Assistant: {content}")
        elif role == "tool":
            tool_name = getattr(m, "name", "tool")
            transcript_lines.append(f"Tool ({tool_name}): {content[:150]}...")
    
    older_transcript = "\n".join(transcript_lines)
    existing_summary = state.get("summary", "").strip()
    
    # Build summarization prompt
    prompt = (
        "You are an expert conversation summarizer. Update the existing summary to incorporate the older dialogue turns.\n"
        "Preserve key facts, user requests, constraints, decisions, and any referenced document details.\n"
        "Keep the updated summary structured, compact, and accurate.\n\n"
        f"[Existing Summary]\n{existing_summary if existing_summary else 'None (First summary).'}\n\n"
        f"[Older Messages to Condense]\n{older_transcript}\n\n"
        "Respond with ONLY the updated summary text."
    )
    
    try:
        provider_cfg = state.get("provider_config", {})
        llm = get_chat_model(
            provider=provider_cfg.get("provider"),
            model_name=provider_cfg.get("model_name"),
            api_key=provider_cfg.get("api_key"),
            base_url=provider_cfg.get("base_url"),
            temperature=0.0,
            streaming=False
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        new_summary = str(response.content).strip()
    except Exception as e:
        logger.error(f"Failed to generate rolling summary: {e}")
        new_summary = existing_summary
    
    # Generate RemoveMessage entries for older messages that have an ID
    remove_actions = [RemoveMessage(id=m.id) for m in older_messages if getattr(m, "id", None)]
    
    return new_summary, remove_actions
