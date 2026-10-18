import os
import shutil
import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.config import UPLOADS_DIR
from app.db.models import DocumentModel, ThreadModel
from app.db.session import get_db
from app.parsers.factory import get_parser_for_file
from app.retrieval.hybrid_store import document_registry
from app.retrieval.router import determine_document_strategy

router = APIRouter(prefix="/api/threads/{thread_id}/documents", tags=["Documents"])

class DocumentUploadResponse(BaseModel):
    id: str
    thread_id: str
    filename: str
    file_type: str
    size_bytes: int
    token_count_estimate: int
    strategy: str  # "DIRECT_CONTEXT" or "TOOL_RETRIEVAL"
    summary_or_toc: str

@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    thread_id: str,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a document for a conversation thread."""
    # Verify thread exists and belongs to user
    stmt = select(ThreadModel).where(ThreadModel.id == thread_id, ThreadModel.user_id == current_user)
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    doc_id = str(uuid.uuid4())
    filename = file.filename or "uploaded_file"
    thread_upload_dir = UPLOADS_DIR / thread_id
    thread_upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = thread_upload_dir / f"{doc_id}_{filename}"
    
    # Save uploaded file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    size_bytes = os.path.getsize(file_path)
    
    # Parse document across supported extensions
    try:
        parser = get_parser_for_file(filename)
        parsed_doc = await parser.parse(file_path, filename)
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse document '{filename}': {str(e)}"
        )
        
    # Determine routing strategy
    strategy = determine_document_strategy(parsed_doc)
    
    # Index large documents in the hybrid store for agentic tool retrieval
    if strategy == "TOOL_RETRIEVAL":
        document_registry.register(doc_id, parsed_doc)
        
    # Save document record to database
    db_doc = DocumentModel(
        id=doc_id,
        thread_id=thread_id,
        user_id=current_user,
        filename=filename,
        file_type=parsed_doc.file_type,
        size_bytes=size_bytes,
        token_count_estimate=parsed_doc.token_estimate,
        strategy=strategy,
        storage_path=str(file_path),
        summary_or_toc=parsed_doc.summary_or_toc
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)
    
    return DocumentUploadResponse(
        id=db_doc.id,
        thread_id=thread_id,
        filename=db_doc.filename,
        file_type=db_doc.file_type,
        size_bytes=db_doc.size_bytes,
        token_count_estimate=db_doc.token_count_estimate,
        strategy=db_doc.strategy,
        summary_or_toc=db_doc.summary_or_toc or ""
    )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    thread_id: str,
    document_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document attached to a thread."""
    stmt = select(DocumentModel).where(
        DocumentModel.id == document_id,
        DocumentModel.thread_id == thread_id,
        DocumentModel.user_id == current_user
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Remove from disk and index registry
    document_registry.remove(document_id)
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except OSError:
            pass
            
    await db.delete(doc)
    await db.commit()
    return None
