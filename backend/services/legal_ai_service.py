"""
Legal AI Service - Main Orchestrator
Ties together all components of the legal AI system
"""
from pathlib import Path
from typing import Optional
import logging
from datetime import datetime

from backend.models.knowledge_schema import QueryResponse
from backend.services.knowledge_indexer import KnowledgeIndexer
from backend.services.bm25_search import BM25SearchEngine
from backend.services.hybrid_search import HybridSearchEngine
from backend.services.query_agent import QueryAgent
from backend.services.folder_manager import FolderManager
from backend.config import settings

logger = logging.getLogger(__name__)


class LegalAIService:
    """
    Main orchestrator for the Legal AI system

    This is the single entry point for:
    - Document indexing
    - Query processing
    - Response generation

    It coordinates:
    - Knowledge indexer (parsing + indexing)
    - BM25 search (keyword)
    - Vector search (semantic)
    - Hybrid search (fusion + reranking)
    - Query agent (understanding + generation)
    """

    def __init__(self, data_dir: Path = None):
        """
        Initialize Legal AI service

        Args:
            data_dir: Directory for storing data and indexes
        """
        self.data_dir = Path(data_dir or settings.DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.indexer = KnowledgeIndexer(data_dir=self.data_dir)
        self.folder_manager = FolderManager(storage_path=self.data_dir / "indexed_folders.json")
        self.hybrid_search: Optional[HybridSearchEngine] = None
        self.query_agent: Optional[QueryAgent] = None

        # State
        self.is_ready = False

        logger.info(f"LegalAIService initialized with data_dir: {self.data_dir}")

    def initialize(self) -> dict:
        """
        Initialize the service

        Loads existing indexes or prepares for new indexing

        Returns:
            Status dictionary
        """
        try:
            logger.info("Initializing LegalAIService...")

            # Try to load existing indexes
            if self.indexer.load_indexes():
                logger.info("Loaded existing indexes")

                # Initialize search engines based on current documents
                self._refresh_search_state()

                if self.is_ready:
                    return {
                        "status": "ready",
                        "message": "Loaded existing knowledge base",
                        "stats": self.get_stats()
                    }
                else:
                    return {
                        "status": "empty",
                        "message": "Knowledge base is empty. Please index documents."
                    }
            else:
                logger.info("No existing indexes found")
                return {
                    "status": "empty",
                    "message": "No knowledge base found. Please index documents."
                }

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return {
                "status": "error",
                "message": f"Initialization failed: {str(e)}"
            }

    def _initialize_search_engines(self):
        """Initialize hybrid search and query agent"""
        logger.info("Initializing search engines...")

        # Initialize hybrid search
        self.hybrid_search = HybridSearchEngine(
            bm25_engine=self.indexer.bm25_engine,
            vector_search_engine=self.indexer,  # KnowledgeIndexer has vector_search method
            cross_encoder_model=None  # TODO: Add cross-encoder if needed
        )

        # Initialize query agent
        self.query_agent = QueryAgent()

        logger.info("Search engines initialized")

    def _refresh_search_state(self):
        """Ensure search engines mirror the current document set."""
        if self.indexer.documents:
            self._initialize_search_engines()
            self.is_ready = True
        else:
            self.hybrid_search = None
            self.query_agent = None
            self.is_ready = False

    def index_documents(
        self,
        doc_dir: Path,
        recursive: bool = True,
        force_reindex: bool = False
    ) -> dict:
        """
        Index documents from a directory

        Args:
            doc_dir: Directory containing documents
            recursive: Include subdirectories
            force_reindex: Reindex even if unchanged

        Returns:
            Indexing statistics
        """
        try:
            logger.info(f"Starting document indexing: {doc_dir}")
            start_time = datetime.now()

            # Run indexing
            stats = self.indexer.index_directory(
                doc_dir=doc_dir,
                recursive=recursive,
                force_reindex=force_reindex
            )

            # Refresh search engines/state based on combined documents
            self._refresh_search_state()

            # Add timing
            elapsed = (datetime.now() - start_time).total_seconds()
            stats["indexing_time_seconds"] = round(elapsed, 2)

            # Track indexed folder
            doc_count = stats.get("indexed_documents", 0)
            self.folder_manager.add_folder(str(doc_dir), document_count=doc_count)

            logger.info(f"Indexing complete in {elapsed:.2f}s")
            return stats

        except Exception as e:
            logger.error(f"Indexing error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Indexing failed: {str(e)}"
            }

    def query(self, query_text: str) -> QueryResponse:
        """
        Process a natural language query

        This is the main entry point for queries. It:
        1. Parses the query to understand intent
        2. Performs hybrid search
        3. Builds a structured response

        Args:
            query_text: User's natural language query

        Returns:
            QueryResponse with results
        """
        if not self.is_ready:
            raise RuntimeError("Service not ready. Please index documents first.")

        logger.info(f"Processing query: {query_text}")
        start_time = datetime.now()

        try:
            # Step 1: Parse query into structured form
            structured_query = self.query_agent.parse_query(query_text)
            logger.info(f"Structured query: intent={structured_query.intent}")

            # Step 2: Perform hybrid search
            search_start = datetime.now()
            search_results = self.hybrid_search.search(
                structured_query,
                score_threshold=0.8,
                strict_threshold=True
            )
            search_time_ms = (datetime.now() - search_start).total_seconds() * 1000

            logger.info(f"Search returned {len(search_results)} results in {search_time_ms:.2f}ms")

            # Step 3: Generate response
            response = self.query_agent.generate_response(
                query=structured_query,
                results=search_results,
                search_time_ms=search_time_ms,
            )

            logger.info(f"Query processed in {response.total_time_ms:.2f}ms")
            return response

        except Exception as e:
            logger.error(f"Query error: {e}", exc_info=True)
            # Return error response
            from backend.models.knowledge_schema import SearchQuery
            return QueryResponse(
                original_query=query_text,
                structured_query=SearchQuery(
                    raw_query=query_text,
                    intent="error",
                    text_query=query_text
                ),
                results=[],
                total_found=0,
                summary=f"An error occurred while processing your query: {str(e)}",
                confidence=0.0,
                cited_chunks=[],
                disclaimer="",
                search_time_ms=0.0,
                generation_time_ms=0.0,
                total_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )

    def get_stats(self) -> dict:
        """
        Get service statistics

        Returns:
            Dictionary with system stats
        """
        stats = {
            "is_ready": self.is_ready,
            "data_dir": str(self.data_dir),
        }

        if self.is_ready:
            stats["indexer"] = self.indexer.get_stats()
            if self.hybrid_search:
                stats["search_engine"] = self.hybrid_search.get_stats()

        return stats

    def get_document_list(self) -> list:
        """
        Get list of indexed documents

        Returns:
            List of document summaries
        """
        if not self.is_ready:
            return []

        return [
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "doctype": doc.doctype,
                "jurisdiction": doc.jurisdiction,
                "parties": doc.parties,
                "effective_date": doc.effective_date.isoformat() if doc.effective_date else None,
                "total_pages": doc.total_pages,
                "total_sections": doc.total_sections,
                "total_chunks": doc.total_chunks,
                "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at else None
            }
            for doc in self.indexer.documents
        ]

    def get_document_details(self, doc_id: str) -> Optional[dict]:
        """
        Get detailed information about a document

        Args:
            doc_id: Document ID

        Returns:
            Document details or None if not found
        """
        if not self.is_ready:
            return None

        doc = self.indexer.bm25_engine.get_document(doc_id)
        if not doc:
            return None

        return {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "file_path": doc.file_path,
            "doctype": doc.doctype,
            "jurisdiction": doc.jurisdiction,
            "parties": doc.parties,
            "creation_date": doc.creation_date.isoformat() if doc.creation_date else None,
            "effective_date": doc.effective_date.isoformat() if doc.effective_date else None,
            "expiration_date": doc.expiration_date.isoformat() if doc.expiration_date else None,
            "version": doc.version,
            "total_pages": doc.total_pages,
            "total_sections": doc.total_sections,
            "section_tree": [s.dict() for s in doc.section_tree],
            "total_chunks": doc.total_chunks,
            "defined_terms": doc.defined_terms,
            "key_clauses": doc.key_clauses,
            "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at else None
        }

    def health_check(self) -> dict:
        """
        Check service health

        Returns:
            Health status
        """
        health = {
            "status": "healthy" if self.is_ready else "not_ready",
            "components": {
                "indexer": self.indexer is not None,
                "bm25": self.indexer.bm25_engine is not None if self.indexer else False,
                "faiss": bool(self.indexer.faiss_index) if self.indexer else False,
                "hybrid_search": self.hybrid_search is not None,
                "query_agent": self.query_agent is not None,
            }
        }

        return health

    def remove_indexed_folder(self, folder_path: Path) -> dict:
        """
        Remove a folder from the knowledge base and tracked list.

        Args:
            folder_path: Folder path to remove.

        Returns:
            Dict describing removal outcome.
        """
        folder_path = Path(folder_path).resolve()
        folder_info = self.folder_manager.get_folder(str(folder_path))

        if not folder_info:
            logger.info(f"Folder not tracked, cannot remove: {folder_path}")
            return {
                "status": "not_found",
                "folder": str(folder_path)
            }

        removal_stats = self.indexer.remove_documents_from_folder(folder_path)

        # Update folder tracking regardless of whether documents existed
        self.folder_manager.remove_folder(str(folder_path))

        # Refresh search state after removal
        self._refresh_search_state()

        return {
            "status": "removed",
            "folder": str(folder_path),
            "removed_documents": removal_stats.get("removed", 0),
            "remaining_documents": removal_stats.get("remaining", 0)
        }
