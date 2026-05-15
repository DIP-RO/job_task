"""Document controller for handling document uploads and processing"""

import logging
import os
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session

from app.models import Document, get_db, DocumentResponse, DocumentCreate, ProcessingResponse
from app.services import DocumentProcessor
from app.workflows import DocumentProcessingWorkflow
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings = Depends(get_settings)
):
    """Upload and process a legal document"""
    try:
        # Validate file extension
        file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"File type .{file_ext} not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Validate file size
        contents = await file.read()
        file_size = len(contents)
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE / (1024*1024):.0f}MB"
            )
        
        # Create uploads directory if it doesn't exist
        os.makedirs("./data/uploads", exist_ok=True)
        
        # Save file
        file_path = f"./data/uploads/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create document record
        doc = Document(
            filename=file.filename,
            original_path=file_path,
            file_type=file_ext,
            processing_status="pending"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        logger.info(f"Document uploaded: {doc.id} ({file.filename})")
        
        return DocumentResponse.from_orm(doc)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/process/{document_id}", response_model=ProcessingResponse)
async def process_document(
    document_id: int,
    draft_type: str = Form("case_summary"),
    db: Session = Depends(get_db),
    settings = Depends(get_settings)
):
    """Process a document through the full pipeline"""
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Mark as processing
        doc.processing_status = "processing"
        db.commit()
        
        # Run workflow
        workflow = DocumentProcessingWorkflow(settings)
        result = workflow.process(document_id, doc.original_path, draft_type)

        # LangGraph may return a dict state, or a nested structure.
        # Normalize to a dict that contains the DocumentProcessingState fields.
        if isinstance(result, dict):
            # Common nesting keys that may contain the state
            state = (
                result.get("state")
                or result.get("data")
                or result.get("document_state")
                or result
            )
        else:
            state = getattr(result, "__dict__", {}) or {}

        document_text = state.get("document_text", "") or ""
        extracted_metadata = state.get("extracted_metadata", {}) or {}
        structured_data = state.get("structured_data", {}) or {}
        ocr_quality = state.get("ocr_quality", 0.0) or 0.0
        processing_status = state.get("processing_status", "failed") or "failed"
        processing_error = state.get("error", None)
        
        # Update document
        doc.raw_text = document_text
        doc.extracted_metadata = extracted_metadata
        doc.structured_data = structured_data
        doc.ocr_quality_score = ocr_quality
        doc.processing_status = processing_status
        doc.processing_error = processing_error
        
        from datetime import datetime
        doc.processed_at = datetime.utcnow()
        
        db.commit()
        
        return ProcessingResponse(
            document_id=document_id,
            status=processing_status,
            message="Document processed successfully" if processing_status != "failed" else "Document processing failed",
            processing_steps=[
                {"step": "document_processed", "status": "success" if processing_status != "failed" else "failed"},
                {"step": "indexed", "status": "success" if processing_status != "failed" else "failed"},
                {"step": "context_retrieved", "status": "success" if processing_status != "failed" else "failed"},
                {"step": "draft_generated", "status": "success" if processing_status != "failed" else "failed"}
            ]
        )
    
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=List[DocumentResponse])
async def list_documents(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """List all documents"""
    documents = db.query(Document).offset(skip).limit(limit).all()
    return [DocumentResponse.from_orm(d) for d in documents]

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get document details"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse.from_orm(doc)

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """Delete a document and all its related drafts and edits"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # First delete all edits for this document's drafts
        from app.models import Edit, Draft
        db.query(Edit).filter(Edit.document_id == document_id).delete(synchronize_session=False)
        # Delete all drafts for this document
        db.query(Draft).filter(Draft.document_id == document_id).delete(synchronize_session=False)
        # Delete the document itself
        db.query(Document).filter(Document.id == document_id).delete(synchronize_session=False)
        db.commit()

        logger.info(f"Document deleted: {document_id} (and all related drafts/edits)")
        return {"status": "deleted", "document_id": document_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))