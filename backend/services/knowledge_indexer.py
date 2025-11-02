"""
Knowledge Indexer
Builds structured knowledge base with BM25 + Vector indexes
"""
from pathlib import Path
from typing import Dict, List, Optional, Set
import logging
import hashlib
import json
from datetime import datetime

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from backend.models.knowledge_schema import StructuredDocument, EnrichedChunk
from backend.services.advanced_parser import LegalDocumentParser
from backend.services.bm25_search import BM25SearchEngine
from backend.config import settings

logger = logging.getLogger(__name__)


class KnowledgeIndexer:
    """
    Unified indexer for structured legal documents

    Builds:
    1. Structured document representations (metadata, sections, entities)
    2. BM25 keyword index
    3. FAISS vector index
    4. Persistent storage for all components

    This is the "knowledge base builder" - transforms raw documents
    into a queryable, metadata-rich knowledge base.
    """

    def __init__(self, data_dir: Path = None):
        """
        Initialize indexer

        Args:
            data_dir: Directory for storing indexes and metadata
        """
        self.data_dir = Path(data_dir or settings.DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Components
        self.parser = LegalDocumentParser()
        self.bm25_engine = BM25SearchEngine()
        self.embedding_model = None
        self.faiss_index = None

        # Storage
        self.documents: List[StructuredDocument] = []
        self.chunks: List[EnrichedChunk] = []

        # Paths
        self.docs_file = self.data_dir / "structured_documents.json"
        self.faiss_index_file = self.data_dir / "faiss_index.bin"
        self.chunks_file = self.data_dir / "enriched_chunks.json"
        self.bm25_dir = self.data_dir / "bm25"

    def initialize_models(self):
        """Load embedding model"""
        if not self.embedding_model:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded")

    def index_directory(
        self,
        doc_dir: Path,
        recursive: bool = True,
        force_reindex: bool = False
    ) -> dict:
        """
        Index all documents in a directory

        Args:
            doc_dir: Directory containing documents
            recursive: Include subdirectories
            force_reindex: Reindex even if document hasn't changed

        Returns:
            Dictionary with indexing statistics
        """
        doc_dir = Path(doc_dir)
        if not doc_dir.exists():
            raise ValueError(f"Directory not found: {doc_dir}")

        logger.info(f"Indexing directory: {doc_dir}")
        logger.info(f"Recursive: {recursive}, Force reindex: {force_reindex}")

        # Initialize models
        self.initialize_models()

        # Load existing documents if not force reindexing
        target_folder = doc_dir.resolve()

        existing_docs_list: List[StructuredDocument] = []
        existing_docs_by_hash: Dict[str, StructuredDocument] = {}

        if self.docs_file.exists():
            logger.info("Loading existing documents...")
            existing_docs_list = self._load_all_documents()
            existing_docs_by_hash = {doc.file_hash: doc for doc in existing_docs_list}
            logger.info(f"Loaded {len(existing_docs_list)} existing documents")

        # Keep documents from other folders so multiple directories share one KB
        remaining_documents: List[StructuredDocument] = []
        removed_existing = 0
        removed_hashes: Set[str] = set()

        for existing_doc in existing_docs_list:
            if self._is_within_folder(existing_doc.file_path, target_folder):
                removed_existing += 1
                removed_hashes.add(existing_doc.file_hash)
                continue
            remaining_documents.append(existing_doc)

        if removed_existing:
            logger.info(f"Preparing to replace {removed_existing} documents from {target_folder}")

        # Find all document files
        extensions = ['.pdf', '.docx', '.txt', '.doc']
        file_pattern = '**/*' if recursive else '*'

        all_files = []
        for ext in extensions:
            all_files.extend(doc_dir.glob(f"{file_pattern}{ext}"))

        logger.info(f"Found {len(all_files)} document files")

        # Parse documents
        new_documents = []
        skipped = 0
        errors = 0

        for file_path in all_files:
            try:
                # Check if already indexed (by hash)
                file_hash = self._compute_file_hash(file_path)

                if not force_reindex and file_hash in existing_docs_by_hash:
                    existing_doc = existing_docs_by_hash[file_hash]

                    if file_hash in removed_hashes:
                        logger.info(f"Skipping (already indexed): {file_path.name}")
                        existing_doc.source_folder = str(target_folder)
                        new_documents.append(existing_doc)
                    else:
                        logger.info(
                            "Skipping duplicate from another folder: %s", file_path.name
                        )

                    skipped += 1
                    continue

                # Parse document
                logger.info(f"Parsing: {file_path.name}")
                structured_doc = self.parser.parse_document(file_path)

                if structured_doc:
                    structured_doc.source_folder = str(target_folder)
                    new_documents.append(structured_doc)
                    logger.info(
                        f"Parsed {file_path.name}: "
                        f"{len(structured_doc.chunks)} chunks, "
                        f"{structured_doc.total_sections} sections"
                    )
                else:
                    logger.warning(f"Failed to parse: {file_path.name}")
                    errors += 1

            except Exception as e:
                logger.error(f"Error parsing {file_path.name}: {e}")
                errors += 1

        if not new_documents:
            logger.warning("No documents to index")
            return {
                "status": "no_documents",
                "total_files": len(all_files),
                "errors": errors
            }

        logger.info(f"Parsed {len(new_documents)} documents ({skipped} skipped, {errors} errors)")

        # Build indexes
        logger.info("Building indexes...")
        self.documents = remaining_documents + new_documents

        # 1. Build BM25 index
        logger.info("Building BM25 index...")
        self.bm25_engine.build_index(self.documents)

        # 2. Build FAISS vector index
        logger.info("Building FAISS vector index...")
        self._build_vector_index()

        # 3. Save everything
        logger.info("Saving indexes...")
        self._save_indexes()

        stats = {
            "status": "success",
            "total_files": len(all_files),
            "indexed_documents": len(new_documents),
            "skipped_documents": skipped,
            "errors": errors,
            "total_chunks": len(self.chunks),
            "bm25_stats": self.bm25_engine.get_stats(),
            "vector_index_size": self.faiss_index.ntotal if self.faiss_index else 0
        }

        logger.info(f"Indexing complete: {stats}")
        return stats

    def _build_vector_index(self):
        """Build FAISS vector index from enriched chunks"""
        # Collect all chunks
        self.chunks = []
        for doc in self.documents:
            self.chunks.extend(doc.chunks)

        if not self.chunks:
            logger.warning("No chunks to index")
            self.faiss_index = None
            return

        logger.info(f"Generating embeddings for {len(self.chunks)} chunks...")

        # Generate embeddings in batches
        batch_size = 32
        all_embeddings = []

        for i in range(0, len(self.chunks), batch_size):
            batch_chunks = self.chunks[i:i + batch_size]
            batch_texts = [chunk.text for chunk in batch_chunks]

            # Generate embeddings
            embeddings = self.embedding_model.encode(
                batch_texts,
                show_progress_bar=False,
                convert_to_numpy=True
            )

            # Store embeddings in chunks
            for chunk, embedding in zip(batch_chunks, embeddings):
                chunk.embedding_vector = embedding.tolist()

            all_embeddings.append(embeddings)

            if (i + batch_size) % 100 == 0:
                logger.info(f"Processed {i + batch_size}/{len(self.chunks)} chunks")

        # Concatenate all embeddings
        embeddings_matrix = np.vstack(all_embeddings).astype('float32')
        logger.info(f"Embeddings shape: {embeddings_matrix.shape}")

        # Build FAISS index
        dimension = embeddings_matrix.shape[1]
        self.faiss_index = faiss.IndexFlatL2(dimension)
        self.faiss_index.add(embeddings_matrix)

        logger.info(f"FAISS index built with {self.faiss_index.ntotal} vectors")

    def _save_indexes(self):
        """Save all indexes and metadata to disk"""
        logger.info("Saving indexes to disk...")

        # 1. Save structured documents
        docs_data = [doc.dict() for doc in self.documents]
        with open(self.docs_file, 'w', encoding='utf-8') as f:
            json.dump(docs_data, f, indent=2, default=str)
        logger.info(f"Saved {len(docs_data)} documents to {self.docs_file}")

        # 2. Save enriched chunks
        chunks_data = [chunk.dict() for chunk in self.chunks]
        with open(self.chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, default=str)
        logger.info(f"Saved {len(chunks_data)} chunks to {self.chunks_file}")

        # 3. Save FAISS index
        if self.faiss_index:
            faiss.write_index(self.faiss_index, str(self.faiss_index_file))
            logger.info(f"Saved FAISS index to {self.faiss_index_file}")

        # 4. Save BM25 index
        self.bm25_dir.mkdir(exist_ok=True)
        self.bm25_engine.save_index(self.bm25_dir)
        logger.info(f"Saved BM25 index to {self.bm25_dir}")

    def load_indexes(self) -> bool:
        """
        Load existing indexes from disk

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Loading indexes from disk...")

            # 1. Load structured documents
            if not self.docs_file.exists():
                logger.warning(f"Documents file not found: {self.docs_file}")
                return False

            with open(self.docs_file, 'r', encoding='utf-8') as f:
                docs_data = json.load(f)

            self.documents = [StructuredDocument(**doc) for doc in docs_data]
            logger.info(f"Loaded {len(self.documents)} documents")

            # 2. Load enriched chunks
            if not self.chunks_file.exists():
                logger.warning(f"Chunks file not found: {self.chunks_file}")
                return False

            with open(self.chunks_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)

            self.chunks = [EnrichedChunk(**chunk) for chunk in chunks_data]
            logger.info(f"Loaded {len(self.chunks)} chunks")

            # 3. Load FAISS index
            if not self.faiss_index_file.exists():
                logger.warning(f"FAISS index not found: {self.faiss_index_file}")
                return False

            self.faiss_index = faiss.read_index(str(self.faiss_index_file))
            logger.info(f"Loaded FAISS index with {self.faiss_index.ntotal} vectors")

            # 4. Load BM25 index
            if not self.bm25_dir.exists():
                logger.warning(f"BM25 index not found: {self.bm25_dir}")
                return False

            self.bm25_engine.load_index(self.bm25_dir, self.documents)
            logger.info("Loaded BM25 index")

            # 5. Load embedding model
            self.initialize_models()

            logger.info("All indexes loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading indexes: {e}")
            return False

    def _load_existing_documents(self) -> dict:
        """
        Load existing documents and return hash map

        Returns:
            Dict mapping file_hash -> StructuredDocument
        """
        docs = self._load_all_documents()
        return {doc.file_hash: doc for doc in docs}

    def _load_all_documents(self) -> List[StructuredDocument]:
        """Load all structured documents from disk."""
        try:
            with open(self.docs_file, 'r', encoding='utf-8') as f:
                docs_data = json.load(f)
            return [StructuredDocument(**doc) for doc in docs_data]
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return []

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def vector_search(
        self,
        query_text: str,
        top_k: int = 20,
        filter_doc_ids: Optional[List[str]] = None
    ) -> List[tuple]:
        """
        Perform vector similarity search

        Args:
            query_text: Query text
            top_k: Number of results
            filter_doc_ids: Optional document ID filter

        Returns:
            List of (EnrichedChunk, similarity_score) tuples
        """
        if not self.faiss_index or not self.embedding_model:
            logger.warning("Vector index not ready")
            return []

        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            [query_text],
            convert_to_numpy=True
        ).astype('float32')

        # Search FAISS
        distances, indices = self.faiss_index.search(query_embedding, top_k * 2)

        # Convert distances to similarity scores (cosine similarity)
        # FAISS L2 distance -> similarity
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= len(self.chunks):
                continue

            chunk = self.chunks[idx]

            # Apply document filter
            if filter_doc_ids and chunk.doc_id not in filter_doc_ids:
                continue

            # Convert L2 distance to similarity (inverse)
            similarity = 1 / (1 + dist)

            results.append((chunk, float(similarity)))

        # Sort and return top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def get_stats(self) -> dict:
        """Get indexer statistics"""
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "faiss_vectors": self.faiss_index.ntotal if self.faiss_index else 0,
            "bm25_stats": self.bm25_engine.get_stats(),
            "data_dir": str(self.data_dir),
            "indexes_loaded": all([
                self.faiss_index is not None,
                self.bm25_engine.bm25_index is not None,
                len(self.documents) > 0
            ])
        }

    @staticmethod
    def _is_within_folder(file_path: str, folder: Path) -> bool:
        """Check if file_path is within folder."""
        try:
            resolved_file = Path(file_path).resolve(strict=False)
            resolved_file.relative_to(folder)
            return True
        except (ValueError, RuntimeError):
            return False

    def remove_documents_from_folder(self, folder_path: Path) -> dict:
        """
        Remove all documents that originate from the given folder.

        Args:
            folder_path: Folder whose documents should be purged.

        Returns:
            Dict with counts of removed and remaining documents.
        """
        folder_path = Path(folder_path).resolve()

        if not self.documents:
            if not self.load_indexes():
                logger.warning("No indexes loaded. Nothing to remove.")
                return {"removed": 0, "remaining": 0}

        remaining_docs: List[StructuredDocument] = []
        removed_docs: List[StructuredDocument] = []

        for doc in self.documents:
            if self._is_within_folder(doc.file_path, folder_path):
                removed_docs.append(doc)
            else:
                remaining_docs.append(doc)

        if not removed_docs:
            logger.info(f"No documents found for folder {folder_path}")
            return {"removed": 0, "remaining": len(self.documents)}

        self.documents = remaining_docs

        logger.info(
            f"Removed {len(removed_docs)} documents originating from {folder_path}"
        )

        # Rebuild indexes with remaining documents
        if self.documents:
            self.initialize_models()
        self.bm25_engine.build_index(self.documents)
        self._build_vector_index()
        self._save_indexes()

        return {"removed": len(removed_docs), "remaining": len(self.documents)}
