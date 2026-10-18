import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

class ThreadModel(Base, TimestampMixin):
    """
    Represents a conversation session/thread scoped to an authenticated user.
    """
    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="New Conversation", nullable=False)
    
    # Rolling summarization state
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    n_turns: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    
    # Model preferences for this thread
    provider: Mapped[str] = mapped_column(String(50), default="gemini", nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), default="gemini-3.5-flash", nullable=False)
    
    # Custom system instructions or extra parameters
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    messages: Mapped[List["MessageModel"]] = relationship(
        "MessageModel", back_populates="thread", cascade="all, delete-orphan", order_by="MessageModel.created_at"
    )
    documents: Mapped[List["DocumentModel"]] = relationship(
        "DocumentModel", back_populates="thread", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_user_updated", "user_id", "updated_at"),
    )

class MessageModel(Base, TimestampMixin):
    """
    An individual message turn (user, assistant, system, or tool call/result).
    """
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id", ondelete="CASCADE"), index=True, nullable=False)
    
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user", "assistant", "system", "tool"
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    
    # Tool execution metadata
    tool_calls: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Turn tracking & summarization marker
    turn_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_summarized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationship
    thread: Mapped["ThreadModel"] = relationship("ThreadModel", back_populates="messages")

    __table_args__ = (
        Index("idx_thread_created", "thread_id", "created_at"),
    )

class DocumentModel(Base, TimestampMixin):
    """
    Metadata for documents attached to a conversation thread.
    """
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count_estimate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Strategy: "DIRECT_CONTEXT" (small file) or "TOOL_RETRIEVAL" (large file)
    strategy: Mapped[str] = mapped_column(String(30), nullable=False)
    
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    summary_or_toc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    thread: Mapped["ThreadModel"] = relationship("ThreadModel", back_populates="documents")
