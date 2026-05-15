"""Test suite for Legal AI Document Processing System"""

import pytest
from pathlib import Path
import tempfile
import os

# Test fixtures

@pytest.fixture
def sample_document():
    """Create a sample text document for testing"""
    content = """
    CASE FACT SUMMARY
    Case Number: 2023-CV-45821
    PARTIES:
    Plaintiff: Johnson Manufacturing Corp
    Defendant: Sterling Logistics LLC
    FACTS:
    Johnson Manufacturing entered into a contract with Sterling Logistics.
    Sterling Logistics failed to meet delivery deadlines.
    Damages exceeded $250,000.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def settings():
    """Get test settings"""
    from app.config import get_settings
    return get_settings()

# Tests

def test_document_processor_text_extraction(sample_document, settings):
    """Test text extraction from plain text files"""
    from app.services import DocumentProcessor
    
    processor = DocumentProcessor(settings)
    result = processor.process_document(sample_document)
    
    assert result["raw_text"] is not None
    assert "CASE FACT SUMMARY" in result["raw_text"]
    assert result["ocr_quality_score"] > 0.5
    assert result["structured_data"]["word_count"] > 0

def test_document_processor_quality_scoring(settings):
    """Test OCR quality scoring logic"""
    from app.services import DocumentProcessor
    
    processor = DocumentProcessor(settings)
    
    # Good quality text
    good_text = "This is a clear, well-formed legal document with proper structure."
    score_good = processor._assess_text_quality(good_text)
    assert score_good > 0.5
    
    # Poor quality text (too short)
    poor_text = "Short"
    score_poor = processor._assess_text_quality(poor_text)
    assert score_poor < 0.5
    
    # Very poor quality (mostly special characters)
    bad_text = "!!!###@@@$$$%%%^^^&&&"
    score_bad = processor._assess_text_quality(bad_text)
    assert score_bad < 0.5

def test_retrieval_service_initialization(settings):
    """Test retrieval service can be initialized"""
    from app.services import RetrievalService
    
    service = RetrievalService(settings)
    assert service.vector_store is not None
    assert service.settings == settings

def test_draft_generator_initialization(settings):
    """Test draft generator can be initialized"""
    from app.services import DraftGenerator
    
    generator = DraftGenerator(settings)
    assert generator.llm is not None
    assert generator.settings == settings

def test_draft_templates_available(settings):
    """Test all draft templates are defined"""
    from app.services import DraftGenerator
    
    generator = DraftGenerator(settings)
    
    for draft_type in ["case_summary", "notice_summary", "checklist", "memo", "title_review"]:
        template = generator._get_draft_template(draft_type)
        assert template is not None
        assert len(template) > 0

def test_edit_learning_service_analysis():
    """Test edit analysis"""
    from app.services import EditLearningService
    from app.config import get_settings
    
    service = EditLearningService(get_settings())
    
    original = "The defendant failed to perform."
    edited = "The defendant failed to perform, specifically stated in the contract [1]."
    
    result = service.analyze_edit(original, edited, "Added citation")
    
    assert result["changes"] is not None
    assert "patterns" in result
    assert result["feedback_category"] is not None

def test_database_models():
    """Test database model creation"""
    from app.models import Document, Draft, Edit
    from sqlalchemy import Column, Integer, String
    
    # Verify models have expected columns
    assert hasattr(Document, 'filename')
    assert hasattr(Document, 'raw_text')
    assert hasattr(Document, 'processing_status')
    
    assert hasattr(Draft, 'draft_content')
    assert hasattr(Draft, 'grounding_score')
    
    assert hasattr(Edit, 'original_content')
    assert hasattr(Edit, 'edited_content')

def test_pydantic_schemas():
    """Test request/response schemas"""
    from app.models import DocumentCreate, DraftResponse, EditCreate
    
    # Test document creation schema
    doc = DocumentCreate(filename="test.pdf", file_type="pdf")
    assert doc.filename == "test.pdf"
    
    # Test edit creation schema
    edit = EditCreate(
        document_id=1,
        draft_id=1,
        original_content="Original",
        edited_content="Edited",
        edit_summary="Test edit"
    )
    assert edit.document_id == 1

def test_workflow_creation(settings):
    """Test LanGraph workflow can be created"""
    from app.workflows import DocumentProcessingWorkflow
    
    workflow = DocumentProcessingWorkflow(settings)
    assert workflow.workflow is not None
    assert workflow.document_processor is not None
    assert workflow.draft_generator is not None

# Integration tests

@pytest.mark.integration
def test_end_to_end_document_processing(sample_document, settings):
    """Test complete document processing pipeline"""
    from app.services import DocumentProcessor
    from app.workflows import DocumentProcessingWorkflow
    
    # Process document
    processor = DocumentProcessor(settings)
    result = processor.process_document(sample_document)
    
    assert result["raw_text"] != ""
    assert result["ocr_quality_score"] > 0.0
    assert "Johnson" in result["raw_text"]

@pytest.mark.integration  
def test_api_health_check(client):
    """Test API health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
