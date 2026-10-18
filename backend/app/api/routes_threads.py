import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.auth.dependencies import get_current_user
from app.db.models import DocumentModel, MessageModel, ThreadModel
from app.db.session import get_db

router = APIRouter(prefix="/api/threads", tags=["Threads"])

class ThreadCreateRequest(BaseModel):
    title: Optional[str] = "New Conversation"
    provider: Optional[str] = "gemini"
    model_name: Optional[str] = "gemini-3.5-flash"
    n_turns: Optional[int] = 5

class ThreadUpdateRequest(BaseModel):
    title: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    n_turns: Optional[int] = None

class MessageSchema(BaseModel):
    id: str
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    turn_index: int
    is_summarized: bool
    created_at: str

class DocumentSchema(BaseModel):
    id: str
    filename: str
    file_type: str
    size_bytes: int
    token_count_estimate: int
    strategy: str
    summary_or_toc: Optional[str] = None
    created_at: str

class ThreadDetailResponse(BaseModel):
    id: str
    title: str
    user_id: str
    summary: str
    n_turns: int
    provider: str
    model_name: str
    created_at: str
    updated_at: str
    messages: List[MessageSchema] = Field(default_factory=list)
    documents: List[DocumentSchema] = Field(default_factory=list)

class ThreadListItem(BaseModel):
    id: str
    title: str
    user_id: str
    summary: str
    n_turns: int
    provider: str
    model_name: str
    created_at: str
    updated_at: str
    message_count: int = 0
    document_count: int = 0

@router.get("", response_model=List[ThreadListItem])
async def list_threads(
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all threads belonging to the authenticated user."""
    stmt = (
        select(ThreadModel)
        .where(ThreadModel.user_id == current_user)
        .options(selectinload(ThreadModel.messages), selectinload(ThreadModel.documents))
        .order_by(ThreadModel.updated_at.desc())
    )
    result = await db.execute(stmt)
    threads = result.scalars().all()
    
    return [
        ThreadListItem(
            id=t.id,
            title=t.title,
            user_id=t.user_id,
            summary=t.summary or "",
            n_turns=t.n_turns,
            provider=t.provider,
            model_name=t.model_name,
            created_at=t.created_at.isoformat(),
            updated_at=t.updated_at.isoformat(),
            message_count=len(t.messages),
            document_count=len(t.documents)
        )
        for t in threads
    ]

@router.post("", response_model=ThreadDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    req: ThreadCreateRequest,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation thread."""
    thread = ThreadModel(
        id=str(uuid.uuid4()),
        user_id=current_user,
        title=req.title or "New Conversation",
        provider=req.provider or "gemini",
        model_name=req.model_name or "gemini-3.5-flash",
        n_turns=req.n_turns or 5,
        summary=""
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    
    return ThreadDetailResponse(
        id=thread.id,
        title=thread.title,
        user_id=thread.user_id,
        summary="",
        n_turns=thread.n_turns,
        provider=thread.provider,
        model_name=thread.model_name,
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
        messages=[],
        documents=[]
    )

@router.get("/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread(
    thread_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get single thread details, messages, and documents."""
    stmt = (
        select(ThreadModel)
        .where(ThreadModel.id == thread_id, ThreadModel.user_id == current_user)
        .options(selectinload(ThreadModel.messages), selectinload(ThreadModel.documents))
    )
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    return ThreadDetailResponse(
        id=thread.id,
        title=thread.title,
        user_id=thread.user_id,
        summary=thread.summary or "",
        n_turns=thread.n_turns,
        provider=thread.provider,
        model_name=thread.model_name,
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
        messages=[
            MessageSchema(
                id=m.id,
                role=m.role,
                content=m.content,
                tool_calls=m.tool_calls,
                tool_call_id=m.tool_call_id,
                turn_index=m.turn_index,
                is_summarized=m.is_summarized,
                created_at=m.created_at.isoformat()
            )
            for m in thread.messages
        ],
        documents=[
            DocumentSchema(
                id=d.id,
                filename=d.filename,
                file_type=d.file_type,
                size_bytes=d.size_bytes,
                token_count_estimate=d.token_count_estimate,
                strategy=d.strategy,
                summary_or_toc=d.summary_or_toc,
                created_at=d.created_at.isoformat()
            )
            for d in thread.documents
        ]
    )

@router.patch("/{thread_id}", response_model=ThreadDetailResponse)
async def update_thread(
    thread_id: str,
    req: ThreadUpdateRequest,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update thread metadata."""
    stmt = (
        select(ThreadModel)
        .where(ThreadModel.id == thread_id, ThreadModel.user_id == current_user)
        .options(selectinload(ThreadModel.messages), selectinload(ThreadModel.documents))
    )
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    if req.title is not None:
        thread.title = req.title
    if req.provider is not None:
        thread.provider = req.provider
    if req.model_name is not None:
        thread.model_name = req.model_name
    if req.n_turns is not None:
        thread.n_turns = req.n_turns
        
    await db.commit()
    await db.refresh(thread)
    return await get_thread(thread_id, current_user, db)

@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a thread and associated messages and documents."""
    stmt = select(ThreadModel).where(ThreadModel.id == thread_id, ThreadModel.user_id == current_user)
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    await db.delete(thread)
    await db.commit()
    return None
