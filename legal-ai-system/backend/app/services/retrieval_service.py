"""Retrieval service for finding relevant evidence in documents"""

import logging
import time
from typing import Dict, List, Any

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class RetrievalService:
    """Retrieve relevant passages and context from processed documents"""

    def __init__(self, settings):
        self.settings = settings
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.vector_store = None
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            self.vector_store = Chroma(
                persist_directory=self.settings.CHROMA_DB_PATH,
                embedding_function=self.embeddings,
                collection_name="legal_documents",
            )
            logger.info("Vector store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")

    @staticmethod
    def _make_safe_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chroma metadata should be JSON-serializable and contain scalar values.
        Convert dict/list values to strings to avoid serialization/runtime issues.
        """
        safe: Dict[str, Any] = {}
        for k, v in (metadata or {}).items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                safe[k] = v
            else:
                # dict/list/other -> string fallback
                safe[k] = str(v)
        return safe

    def add_document_to_index(self, doc_id: int, raw_text: str, metadata: Dict[str, Any]) -> bool:
        """
        Add document to vector index

        Args:
            doc_id: Document ID
            raw_text: Raw extracted text
            metadata: Document metadata

        Returns:
            Success status
        """
        try:
            if not raw_text or not raw_text.strip():
                logger.warning(f"Skipping indexing for doc_id={doc_id}: empty raw_text")
                return False

            if self.vector_store is None:
                logger.error("Vector store is not initialized; cannot add document to index")
                return False

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.settings.CHUNK_SIZE,
                chunk_overlap=self.settings.CHUNK_OVERLAP,
                separators=["\n\n", "\n", " ", ""],
            )

            chunks = splitter.split_text(raw_text)
            if not chunks:
                logger.warning(f"No chunks created for doc_id={doc_id}")
                return False

            documents: List[Document] = []
            for idx, chunk in enumerate(chunks):
                raw_metadata = {
                    "doc_id": doc_id,
                    "chunk_index": idx,
                    "source": (metadata or {}).get("filename", "unknown"),
                    **(metadata or {}),
                }
                safe_metadata = self._make_safe_metadata(raw_metadata)
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata=safe_metadata,
                    )
                )

            ids = [f"{doc_id}_{i}" for i in range(len(documents))]
            self.vector_store.add_documents(documents, ids=ids)

            logger.info(f"Added {len(documents)} chunks for document {doc_id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to add document to index (doc_id={doc_id}): {e}")
            return False

    def retrieve_context(self, query: str, doc_id: int = None, top_k: int = None) -> Dict[str, Any]:
        """
        Retrieve relevant context for a query - only returns passages that meet minimum similarity threshold
        to ensure only high-quality, relevant context is passed to generation.

        Args:
            query: Search query or question
            doc_id: Optional document ID to filter results
            top_k: Number of results to return

        Returns:
            Dictionary with relevant passages and metadata
        """
        start_time = time.time()
        top_k = top_k or self.settings.TOP_K_RESULTS

        try:
            filter_dict = None
            if doc_id is not None:
                filter_dict = {"doc_id": doc_id}

            # Request more results than needed to filter for quality
            results = self.vector_store.similarity_search_with_score(
                query,
                k=top_k * 2,  # Get extra to filter
                filter=filter_dict,
            )

            passages: List[Dict[str, Any]] = []
            for doc, score in results:
                # Chroma/LangChain score semantics vary:
                # - sometimes it's a distance (lower is better)
                # - sometimes it's a similarity (higher is better)
                # Heuristic:
                # - if score looks like similarity in [0, 1], use it directly
                # - otherwise treat it like distance and convert (higher is better)
                if 0.0 <= score <= 1.0:
                    similarity = float(score)
                else:
                    similarity = 1.0 - float(score)

                # STRICT FILTER: Only include passages that meet or exceed threshold
                # This ensures only the most relevant context is ever used for generation
                if similarity >= self.settings.SIMILARITY_THRESHOLD:
                    passages.append(
                        {
                            "text": doc.page_content,
                            "metadata": doc.metadata,
                            "similarity_score": float(similarity),
                            "chunk_index": doc.metadata.get("chunk_index", -1),
                            "doc_id": doc.metadata.get("doc_id", -1),
                            "source": doc.metadata.get("source", "unknown"),
                            "inspectable": True,  # Flag that this evidence has all metadata needed for review
                        }
                    )

            processing_time = (time.time() - start_time) * 1000
            return {
                "relevant_passages": passages,
                "total_results": len(passages),
                "query": query,
                "processing_time_ms": processing_time,
                "threshold_applied": self.settings.SIMILARITY_THRESHOLD,
            }

        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            return {
                "relevant_passages": [],
                "total_results": 0,
                "query": query,
                "processing_time_ms": (time.time() - start_time) * 1000,
                "error": str(e),
            }

    def retrieve_multi_query(self, queries: List[str], doc_id: int = None) -> Dict[str, Any]:
        """
        Retrieve context for multiple queries
        """
        all_passages: Dict[str, Dict[str, Any]] = {}
        all_results: List[Dict[str, Any]] = []

        for query in queries:
            result = self.retrieve_context(query, doc_id)
            all_results.append(result)

            for passage in result["relevant_passages"]:
                passage_text = passage["text"]
                if passage_text not in all_passages:
                    all_passages[passage_text] = passage

        return {
            "queries": queries,
            "relevant_passages": list(all_passages.values()),
            "total_results": len(all_passages),
            "per_query_results": all_results,
        }

    def get_document_summary(self, doc_id: int) -> Dict[str, Any]:
        """Get summary of key topics in a document"""
        try:
            result = self.retrieve_context(
                "main topics key facts important summary",
                doc_id,
                top_k=3,
            )
            return {
                "doc_id": doc_id,
                "key_passages": result["relevant_passages"],
                "coverage": len(result["relevant_passages"]) > 0,
            }
        except Exception as e:
            logger.error(f"Failed to get document summary: {str(e)}")
            return {"doc_id": doc_id, "error": str(e)}