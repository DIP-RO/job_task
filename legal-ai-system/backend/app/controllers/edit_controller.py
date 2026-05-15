"""Edit controller for tracking and learning from edits"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import Document, Draft, Edit, get_db, EditResponse, EditCreate
from app.services import EditLearningService
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/edits", tags=["edits"])

@router.post("/record", response_model=EditResponse)
async def record_edit(
    edit_request: EditCreate,
    db: Session = Depends(get_db),
    settings = Depends(get_settings)
):
    """Record an edit to a draft for learning"""
    try:
        # Verify draft exists
        draft = db.query(Draft).filter(Draft.id == edit_request.draft_id).first()
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        # Analyze the edit
        edit_learning = EditLearningService(settings)
        analysis = edit_learning.analyze_edit(
            edit_request.original_content,
            edit_request.edited_content,
            edit_request.reasoning,
            edit_request.feedback_category
        )
        
        # Save edit record
        changes = analysis.get("changes", [])
        first_change = changes[0] if changes else {}
        change_type = first_change.get("modification_type", "unknown")
        extracted_patterns = analysis.get("patterns", [])
        feedback_category = analysis.get("feedback_category")

        logger.info(
            "Recording edit with fields: %s",
            {
                "document_id": edit_request.document_id,
                "draft_id": edit_request.draft_id,
                "change_type": change_type,
                "feedback_category": feedback_category,
                "extracted_patterns_is_list": isinstance(extracted_patterns, list),
                "extracted_patterns_len": len(extracted_patterns) if isinstance(extracted_patterns, list) else None,
            },
        )

        edit = Edit(
            document_id=edit_request.document_id,
            draft_id=edit_request.draft_id,
            original_content=edit_request.original_content,
            edited_content=edit_request.edited_content,
            edit_summary=edit_request.edit_summary,
            change_type=change_type,
            reasoning=edit_request.reasoning,
            extracted_patterns=extracted_patterns,
            feedback_category=feedback_category,
        )
        
        db.add(edit)
        db.commit()
        db.refresh(edit)
        
        logger.info(f"Edit recorded: {edit.id}")
        
        return EditResponse.from_orm(edit)
    
    except Exception as e:
        logger.exception("Edit recording failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/draft/{draft_id}", response_model=List[EditResponse])
async def get_edits_for_draft(
    draft_id: int,
    db: Session = Depends(get_db)
):
    """Get all edits for a draft"""
    edits = db.query(Edit).filter(Edit.draft_id == draft_id).all()
    return [EditResponse.from_orm(e) for e in edits]

@router.get("/document/{document_id}", response_model=List[EditResponse])
async def get_edits_for_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get all edits for a document"""
    edits = db.query(Edit).filter(Edit.document_id == document_id).all()
    return [EditResponse.from_orm(e) for e in edits]

@router.get("/patterns")
async def get_learned_patterns(settings = Depends(get_settings)):
    """Get patterns learned from all edits"""
    try:
        edit_learning = EditLearningService(settings)
        patterns = edit_learning.get_learned_patterns()
        
        return {
            "patterns": patterns,
            "count": len(patterns)
        }
    except Exception as e:
        logger.error(f"Failed to get patterns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
