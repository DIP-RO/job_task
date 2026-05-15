"""LanGraph workflow for orchestrating the document processing pipeline"""

import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from app.services import (
    DocumentProcessor,
    RetrievalService,
    DraftGenerator,
    EditLearningService
)
from app.config import Settings

logger = logging.getLogger(__name__)

class DocumentProcessingState(BaseModel):
    """State for document processing workflow"""
    document_id: int
    file_path: str
    document_text: str = ""
    extracted_metadata: Dict[str, Any] = {}
    structured_data: Dict[str, Any] = {}
    ocr_quality: float = 0.0
    processing_status: str = "pending"
    error: str = None
    
    draft_type: str = "case_summary"
    retrieved_passages: List[Dict[str, Any]] = Field(default_factory=list)
    draft_content: str = ""
    grounding_score: float = 0.0
    completeness_score: float = 0.0
    
    learned_patterns: List[str] = Field(default_factory=list)

class DocumentProcessingWorkflow:
    """Orchestrate document processing workflow using LanGraph"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.document_processor = DocumentProcessor(settings)
        self.retrieval_service = RetrievalService(settings)
        self.draft_generator = DraftGenerator(settings)
        self.edit_learning_service = EditLearningService(settings)
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """Build the LanGraph workflow"""
        
        workflow = StateGraph(DocumentProcessingState)
        
        # Add nodes
        workflow.add_node("process_document", self._process_document_node)
        workflow.add_node("index_document", self._index_document_node)
        workflow.add_node("retrieve_context", self._retrieve_context_node)
        workflow.add_node("generate_draft", self._generate_draft_node)
        workflow.add_node("evaluate_output", self._evaluate_output_node)
        
        # Add edges
        workflow.add_edge("process_document", "index_document")
        workflow.add_edge("index_document", "retrieve_context")
        workflow.add_edge("retrieve_context", "generate_draft")
        workflow.add_edge("generate_draft", "evaluate_output")
        workflow.add_edge("evaluate_output", END)
        
        # Set entry point
        workflow.set_entry_point("process_document")
        
        return workflow.compile()
    
    def _process_document_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Node: Process document (OCR, extraction)"""
        logger.info(f"Processing document {state.document_id}")
        
        try:
            result = self.document_processor.process_document(state.file_path)
            
            state.document_text = result.get("raw_text", "")
            state.extracted_metadata = result.get("extracted_metadata", {})
            state.structured_data = result.get("structured_data", {})
            state.ocr_quality = result.get("ocr_quality_score", 0.0)
            state.processing_status = "document_processed"
            
            logger.info(f"Document {state.document_id} processed with OCR quality: {state.ocr_quality}")
            
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            state.error = str(e)
            state.processing_status = "failed"
        
        return state
    
    def _index_document_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Node: Index document in vector store"""
        logger.info(f"Indexing document {state.document_id}")
        
        try:
            if state.error or not state.document_text:
                logger.warning(f"Skipping indexing for document {state.document_id}: no valid text")
                return state
            
            success = self.retrieval_service.add_document_to_index(
                state.document_id,
                state.document_text,
                {
                    "filename": state.file_path,
                    "ocr_quality": state.ocr_quality,
                    **state.extracted_metadata
                }
            )
            
            state.processing_status = "indexed"
            logger.info(f"Document {state.document_id} indexed: {success}")
            
        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            state.error = str(e)
        
        return state
    
    def _retrieve_context_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Node: Retrieve relevant context"""
        logger.info(f"Retrieving context for document {state.document_id}")
        
        try:
            if state.error or not state.document_text:
                return state
            
            # Create query based on document content
            query = self._create_retrieval_query(state)
            
            result = self.retrieval_service.retrieve_context(
                query,
                doc_id=state.document_id,
                top_k=self.settings.TOP_K_RESULTS
            )
            
            state.retrieved_passages = result.get("relevant_passages", [])
            state.processing_status = "context_retrieved"
            
            logger.info(f"Retrieved {len(state.retrieved_passages)} passages")
            
        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            state.error = str(e)
        
        return state
    
    def _generate_draft_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Node: Generate draft"""
        logger.info(f"Generating draft for document {state.document_id}")
        
        try:
            if state.error or not state.document_text:
                return state
            
            # Get learned patterns
            state.learned_patterns = self.edit_learning_service.get_learned_patterns()
            
            result = self.draft_generator.generate_draft(
                state.document_text,
                state.retrieved_passages,
                draft_type=state.draft_type,
                learned_patterns=state.learned_patterns
            )
            
            state.draft_content = result.get("draft_content", "")
            state.grounding_score = result.get("grounding_score", 0.0)
            state.completeness_score = result.get("completeness_score", 0.0)
            state.processing_status = "draft_generated"
            
            logger.info(f"Draft generated with grounding score: {state.grounding_score}")
            
        except Exception as e:
            logger.error(f"Draft generation failed: {str(e)}")
            state.error = str(e)
        
        return state
    
    def _evaluate_output_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Node: Evaluate output quality"""
        logger.info(f"Evaluating output for document {state.document_id}")
        
        try:
            # Basic quality checks
            if not state.draft_content:
                logger.warning("No draft content to evaluate")
                return state
            
            # Check if grounding is sufficient
            if state.grounding_score < 0.5:
                logger.warning(f"Low grounding score: {state.grounding_score}")
            
            # Check if completeness is sufficient
            if state.completeness_score < 0.5:
                logger.warning(f"Low completeness score: {state.completeness_score}")
            
            state.processing_status = "completed"
            
        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            state.error = str(e)
        
        return state
    
    def _create_retrieval_query(self, state: DocumentProcessingState) -> str:
        """Create a good retrieval query from document"""
        # Extract key topics
        metadata = state.extracted_metadata
        phrases = []
        
        if "key_phrases" in state.structured_data:
            phrases = state.structured_data["key_phrases"][:3]
        
        if phrases:
            query = " ".join(phrases) + " summary facts"
        else:
            query = "main topics facts summary"
        
        return query
    
    def process(self, document_id: int, file_path: str, draft_type: str = None) -> DocumentProcessingState:
        """Run the complete workflow"""
        state = DocumentProcessingState(
            document_id=document_id,
            file_path=file_path,
            draft_type=draft_type or self.settings.DRAFT_TYPE
        )

        logger.info(f"Starting workflow for document {document_id}")
        result = self.workflow.invoke(state)

        # LangGraph can return a dict-like state.
        if isinstance(result, dict):
            state_dict = (
                result.get("state")
                or result.get("data")
                or result.get("document_state")
                or result
            )
            processing_status = state_dict.get("processing_status", "completed")
            logger.info(f"Workflow completed with status: {processing_status}")
            return state_dict  # controller will normalize

        processing_status = getattr(result, "processing_status", "completed")
        logger.info(f"Workflow completed with status: {processing_status}")

        return result