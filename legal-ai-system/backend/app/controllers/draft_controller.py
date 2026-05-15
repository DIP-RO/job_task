"""Draft controller for draft generation and management"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import Document, Draft, Edit, get_db, DraftResponse, GenerationRequest
from app.services import DraftGenerator, RetrievalService, EditLearningService
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/drafts", tags=["drafts"])

@router.post("/generate", response_model=DraftResponse)
async def generate_draft(
    request: GenerationRequest,
    db: Session = Depends(get_db),
    settings = Depends(get_settings)
):
    """Generate a draft for a document"""
    try:
        doc = db.query(Document).filter(Document.id == request.document_id).first()
        if not doc or not doc.raw_text:
            raise HTTPException(status_code=404, detail="Document not found or not processed")
        
        # Generate DRAFT-TYPE SPECIFIC retrieval queries to get the MOST relevant context
        # This ensures we pull exactly what's needed for each draft type, improving relevance
        draft_type_queries = {
            "case_summary": [
                "parties involved plaintiff defendant",
                "key dates deadlines timeline",
                "core facts allegations claims",
                "legal causes of action damages",
                "current status procedural history"
            ],
            "notice_summary": [
                "issuing authority court agency",
                "deadlines dates response required",
                "actions that must be taken",
                "parties affected responsible persons",
                "consequences penalties non-compliance"
            ],
            "checklist": [
                "requirements compliance verify",
                "deadlines dates submit file",
                "documents needed evidence",
                "responsibilities who must do what",
                "risks penalties non-compliance"
            ],
            "memo": [
                "executive summary key issues",
                "factual background history",
                "legal analysis arguments",
                "recommendations actions items",
                "risks mitigation strategies"
            ],
            "title_review": [
                "property description location",
                "liens encumbrances clouds",
                "ownership history transfers",
                "issues defects title problems",
                "recommendations cure fixes"
            ]
        }
        
        # Get the right queries for this draft type, fallback to base queries
        queries = draft_type_queries.get(request.draft_type, [
            "main facts key information",
            "important dates parties",
            "legal claims requirements"
        ])
        
        # Use multi-query retrieval to get comprehensive context from multiple angles
        retrieval_service = RetrievalService(settings)
        retrieval_result = retrieval_service.retrieve_multi_query(
            queries,
            doc_id=request.document_id
        )
        
        # Get learned patterns if requested - REAL IMPROVEMENT LOOP
        system_prompt_additions = ""
        learned_patterns = []
        if request.use_learned_patterns:
            edit_learning = EditLearningService(settings)
            improvements = edit_learning.get_improvements_for_draft()
            system_prompt_additions = improvements["system_prompt_additions"]
            learned_patterns = improvements["applicable_patterns"]
            logger.info(f"Applying {len(learned_patterns)} learned improvements to draft")
        
        # Generate draft with the multi-query retrieved passages and injected learned improvements
        draft_generator = DraftGenerator(settings)
        generation_result = draft_generator.generate_draft(
            doc.raw_text,
            retrieval_result["relevant_passages"],  # Already deduplicated from multi-query
            draft_type=request.draft_type,
            learned_patterns=learned_patterns,
            system_prompt_additions=system_prompt_additions
        )
        
        # Log generation result for debugging
        logger.info(f"Generation result: {generation_result}")
        logger.info(f"Draft content length: {len(generation_result['draft_content'])}")

        # Prevent 200 responses with empty draft_content (frontend shows blank)
        if (
            generation_result.get("status") == "blocked"
            or not generation_result.get("draft_content")
            or len(generation_result.get("draft_content", "")) == 0
        ):
            error_msg = generation_result.get(
                "error",
                "Draft generation blocked or produced empty draft_content."
            )
            raise HTTPException(status_code=422, detail=error_msg)

        # Save draft to database
        draft = Draft(
            document_id=request.document_id,
            draft_type=request.draft_type,
            draft_content=generation_result["draft_content"],
            supporting_evidence=generation_result["supporting_evidence"],
            evidence_citations=generation_result.get("structured_draft", {}).get("citations", []),
            grounding_score=generation_result["grounding_score"],
            completeness_score=generation_result["completeness_score"]
        )
        
        db.add(draft)
        db.commit()
        db.refresh(draft)
        
        logger.info(f"Draft generated: {draft.id}")
        
        return DraftResponse.from_orm(draft)
    
    except Exception as e:
        logger.error(f"Draft generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: int,
    db: Session = Depends(get_db)
):
    """Get draft details"""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return DraftResponse.from_orm(draft)

@router.get("/document/{document_id}", response_model=List[DraftResponse])
async def get_drafts_for_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get all drafts for a document"""
    drafts = db.query(Draft).filter(Draft.document_id == document_id).all()
    return [DraftResponse.from_orm(d) for d in drafts]


@router.put("/{draft_id}", response_model=DraftResponse)
async def update_draft(
    draft_id: int,
    updates: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Update a draft - save edits and changes"""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Update allowed fields
    allowed_fields = ["draft_content", "draft_type", "supporting_evidence", "evidence_citations"]
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(draft, field, value)
    
    # Increment version
    draft.version += 1
    db.commit()
    db.refresh(draft)
    logger.info(f"Draft updated: {draft_id}, version: {draft.version}")
    return DraftResponse.from_orm(draft)

@router.delete("/{draft_id}")
async def delete_draft(
    draft_id: int,
    db: Session = Depends(get_db),
):
    """Delete a draft and its related edits"""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    try:
        # Explicitly delete edits first (no cascade configured)
        db.query(Edit).filter(Edit.draft_id == draft_id).delete(synchronize_session=False)

        db.query(Draft).filter(Draft.id == draft_id).delete(synchronize_session=False)
        db.commit()

        logger.info(f"Draft deleted: {draft_id}")
        return {"status": "deleted", "draft_id": draft_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete draft {draft_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))