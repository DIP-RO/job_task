from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Document Schemas
class DocumentCreate(BaseModel):
    """Schema for creating a new document"""
    filename: str
    file_type: str

class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: int
    filename: str
    file_type: str
    processing_status: str
    ocr_quality_score: Optional[float] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    extracted_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Draft Schemas
class DraftCreate(BaseModel):
    """Schema for creating a draft"""
    document_id: int
    draft_type: str = "case_summary"

class DraftResponse(BaseModel):
    """Schema for draft response"""
    id: int
    document_id: int
    draft_type: str
    draft_content: str
    grounding_score: float
    completeness_score: float
    supporting_evidence: List[Dict[str, Any]]
    evidence_citations: List[Dict[str, Any]]
    created_at: datetime
    version: int

    class Config:
        from_attributes = True


# Edit Schemas
class EditCreate(BaseModel):
    """Schema for creating an edit record"""
    document_id: int
    draft_id: int
    original_content: str
    edited_content: str
    edit_summary: str
    reasoning: Optional[str] = None
    feedback_category: Optional[str] = None

class EditResponse(BaseModel):
    """Schema for edit response"""
    id: int
    document_id: int
    draft_id: int
    original_content: str
    edited_content: str
    edit_summary: str
    change_type: Optional[str] = None
    feedback_category: Optional[str] = None
    extracted_patterns: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Retrieval Schemas
class RetrievalContextResponse(BaseModel):
    """Schema for retrieval context"""
    relevant_passages: List[Dict[str, Any]] = Field(
        ..., description="List of relevant passages with scores and metadata"
    )
    total_results: int
    processing_time_ms: float

class GenerationRequest(BaseModel):
    """Schema for generation request"""
    document_id: int
    draft_type: str = "case_summary"
    use_learned_patterns: bool = True
    allow_unsafe: bool = False  # If true, bypass high-similarity evidence filter (use with caution)

class ProcessingResponse(BaseModel):
    """Schema for processing response"""
    document_id: int
    status: str
    message: str
    processing_steps: List[Dict[str, Any]]
