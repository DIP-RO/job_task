from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Document(Base):
    """Document entity for storing processed legal documents"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), index=True)
    original_path = Column(String(500))
    file_type = Column(String(20))  # pdf, txt, docx, etc.
    
    # Extracted content
    raw_text = Column(Text)
    extracted_metadata = Column(JSON)  # Title, date, parties, etc.
    structured_data = Column(JSON)  # Sections, entities, etc.
    
    # Processing information
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    ocr_quality_score = Column(Float, nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    drafts = relationship("Draft", back_populates="document")
    edits = relationship("Edit", back_populates="document")
    processing_logs = relationship("ProcessingLog", back_populates="document")


class Draft(Base):
    """Draft entity for storing generated legal drafts"""
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), index=True)
    
    # Draft content
    draft_type = Column(String(50))  # case_summary, notice, checklist, memo, title_review
    draft_content = Column(Text)
    supporting_evidence = Column(JSON)  # Array of {text: str, page: int, confidence: float}
    evidence_citations = Column(JSON)  # Array of {ref_id: str, quote: str}
    
    # Quality metrics
    grounding_score = Column(Float)  # 0-1 indicating how well grounded
    completeness_score = Column(Float)  # 0-1 indicating completeness
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    
    # Relationships
    document = relationship("Document", back_populates="drafts")
    edits = relationship("Edit", back_populates="draft")


class Edit(Base):
    """Edit entity for tracking operator edits to drafts"""
    __tablename__ = "edits"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), index=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), index=True)
    
    # Edit information
    original_content = Column(Text)  # Original draft text
    edited_content = Column(Text)  # Modified draft text
    edit_summary = Column(Text)  # What was changed and why
    change_type = Column(String(50))  # addition, deletion, modification, reordering
    
    # Learning data
    reasoning = Column(Text)  # Why the operator made this edit
    extracted_patterns = Column(JSON)  # Patterns learned from this edit
    feedback_category = Column(String(100))  # grounding, clarity, completeness, etc.
    
    # Tracking
    operator_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_to_generation = Column(Boolean, default=False)
    
    # Relationships
    document = relationship("Document", back_populates="edits")
    draft = relationship("Draft", back_populates="edits")


class ProcessingLog(Base):
    """Processing log entity for tracking document processing steps"""
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), index=True)
    
    # Log information
    step = Column(String(100))  # extraction, retrieval, generation, etc.
    status = Column(String(50))  # success, warning, error
    message = Column(Text)
    duration_ms = Column(Integer)  # Duration in milliseconds
    
    # Detailed data
    step_metadata = Column(JSON)  # Step-specific metadata
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="processing_logs")
