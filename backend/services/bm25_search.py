"""
BM25 Search Engine for Legal Documents
Keyword-based retrieval using BM25 algorithm
"""
from typing import List, Dict, Tuple, Optional
from rank_bm25 import BM25Okapi
import re
from pathlib import Path
import json
import logging

from backend.models.knowledge_schema import (
    StructuredDocument,
    EnrichedChunk,
    SearchQuery
)

logger = logging.getLogger(__name__)


class BM25SearchEngine:
    """
    BM25-based keyword search engine

    Features:
    - Tokenization with legal term preservation
    - BM25 scoring (Okapi variant)
    - Chunk-level search with document context
    - Term frequency caching for fast retrieval
    """

    def __init__(self):
        self.bm25_index: Optional[BM25Okapi] = None
        self.chunks: List[EnrichedChunk] = []
        self.documents: Dict[str, StructuredDocument] = {}
        self.tokenized_corpus: List[List[str]] = []

        # Legal-specific stop words (minimal - preserve legal terms)
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
            'that', 'the', 'to', 'was', 'will', 'with'
        }

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text with legal term preservation

        Preserves:
        - Section numbers (§5.2, Section 5.2)
        - Legal citations (17 U.S.C. §101)
        - Money amounts ($1,000,000)
        - Dates (January 1, 2024)
        - Compound legal terms (non-compete, force-majeure)
        """
        # Lowercase
        text = text.lower()

        # Preserve special patterns
        # Section references: §5.2, section 5.2
        text = re.sub(r'§\s*(\d+(?:\.\d+)*)', r'section_\1', text)
        text = re.sub(r'\bsection\s+(\d+(?:\.\d+)*)', r'section_\1', text)

        # Money amounts: $1,000,000 -> usd_1000000
        text = re.sub(r'\$\s*([\d,]+(?:\.\d+)?)', lambda m: f"usd_{m.group(1).replace(',', '')}", text)

        # Dates: normalize to year if present
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, text)

        # Hyphenated legal terms: preserve
        # (non-compete, force-majeure, etc.)
        text = re.sub(r'([a-z]+)-([a-z]+)', r'\1_\2', text)

        # Tokenize
        tokens = re.findall(r'\b[\w_]+\b', text)

        # Remove stop words but keep legal terms
        tokens = [
            t for t in tokens
            if t not in self.stop_words or len(t) > 3 or '_' in t
        ]

        return tokens

    def build_index(self, documents: List[StructuredDocument]) -> None:
        """
        Build BM25 index from structured documents

        Args:
            documents: List of structured documents with enriched chunks
        """
        logger.info(f"Building BM25 index for {len(documents)} documents...")

        self.chunks = []
        self.documents = {}
        self.tokenized_corpus = []

        for doc in documents:
            self.documents[doc.doc_id] = doc

            for chunk in doc.chunks:
                self.chunks.append(chunk)

                # Tokenize chunk text
                tokens = self.tokenize(chunk.text)
                self.tokenized_corpus.append(tokens)

                # Cache term frequencies in chunk metadata
                chunk.term_frequencies = {}
                for token in tokens:
                    chunk.term_frequencies[token] = chunk.term_frequencies.get(token, 0) + 1

        # Build BM25 index
        if self.tokenized_corpus:
            self.bm25_index = BM25Okapi(self.tokenized_corpus)
            logger.info(f"BM25 index built with {len(self.chunks)} chunks")
        else:
            logger.warning("No chunks found for BM25 indexing")
            self.bm25_index = None

    def search(
        self,
        query: str,
        top_k: int = 20,
        filter_doc_ids: Optional[List[str]] = None
    ) -> List[Tuple[EnrichedChunk, float]]:
        """
        Search using BM25 algorithm

        Args:
            query: Search query string
            top_k: Number of top results to return
            filter_doc_ids: Optional list of document IDs to filter by

        Returns:
            List of (chunk, bm25_score) tuples, sorted by score descending
        """
        if not self.bm25_index or not self.chunks:
            logger.warning("BM25 index not built")
            return []

        # Tokenize query
        query_tokens = self.tokenize(query)
        if not query_tokens:
            logger.warning("Query tokenization resulted in empty tokens")
            return []

        logger.info(f"BM25 search for query tokens: {query_tokens[:10]}")

        # Get BM25 scores
        scores = self.bm25_index.get_scores(query_tokens)

        # Combine chunks with scores
        results = []
        for idx, score in enumerate(scores):
            chunk = self.chunks[idx]

            # Apply document filter if provided
            if filter_doc_ids and chunk.doc_id not in filter_doc_ids:
                continue

            if score > 0:  # Only include chunks with positive scores
                results.append((chunk, float(score)))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)

        # Return top-k
        top_results = results[:top_k]
        logger.info(f"BM25 search returned {len(top_results)} results (top {top_k})")

        return top_results

    def search_with_filters(
        self,
        structured_query: SearchQuery
    ) -> List[Tuple[EnrichedChunk, float]]:
        """
        Search with structured query filters

        Applies filters:
        - Document types
        - Jurisdictions
        - Date ranges
        - Parties
        - Required terms
        - Excluded terms

        Args:
            structured_query: Structured search query with filters

        Returns:
            List of (chunk, bm25_score) tuples
        """
        # Get candidate document IDs based on filters
        candidate_doc_ids = self._apply_filters(structured_query)

        # Build query with required/excluded terms
        query_text = structured_query.text_query

        # Add required terms
        if structured_query.required_terms:
            query_text += " " + " ".join(structured_query.required_terms)

        # Perform BM25 search with document filter
        results = self.search(
            query=query_text,
            top_k=structured_query.top_k * 2,  # Get more for re-ranking
            filter_doc_ids=candidate_doc_ids if candidate_doc_ids else None
        )

        # Apply excluded terms filter
        if structured_query.excluded_terms:
            excluded_tokens = set()
            for term in structured_query.excluded_terms:
                excluded_tokens.update(self.tokenize(term))

            results = [
                (chunk, score) for chunk, score in results
                if not any(
                    token in self.tokenize(chunk.text)
                    for token in excluded_tokens
                )
            ]

        return results

    def _apply_filters(self, query: SearchQuery) -> Optional[List[str]]:
        """
        Apply metadata filters to get candidate document IDs

        Returns:
            List of document IDs that match filters, or None for no filter
        """
        candidate_docs = list(self.documents.values())

        # Filter by document type
        if query.doctypes:
            candidate_docs = [
                doc for doc in candidate_docs
                if doc.doctype in query.doctypes
            ]

        # Filter by jurisdiction
        if query.jurisdictions:
            candidate_docs = [
                doc for doc in candidate_docs
                if doc.jurisdiction in query.jurisdictions
            ]

        # Filter by date range
        if query.date_range:
            start_date, end_date = query.date_range
            candidate_docs = [
                doc for doc in candidate_docs
                if doc.effective_date and start_date <= doc.effective_date <= end_date
            ]

        # Filter by parties
        if query.parties:
            candidate_docs = [
                doc for doc in candidate_docs
                if any(party.lower() in [p.lower() for p in doc.parties] for party in query.parties)
            ]

        # Return document IDs
        if len(candidate_docs) < len(self.documents):
            return [doc.doc_id for doc in candidate_docs]
        else:
            return None  # No filtering needed

    def get_document(self, doc_id: str) -> Optional[StructuredDocument]:
        """Get document by ID"""
        return self.documents.get(doc_id)

    def get_chunk_context(
        self,
        chunk: EnrichedChunk,
        context_chunks: int = 1
    ) -> List[EnrichedChunk]:
        """
        Get surrounding chunks for context

        Args:
            chunk: Target chunk
            context_chunks: Number of chunks before/after to include

        Returns:
            List of chunks including target and context
        """
        doc = self.documents.get(chunk.doc_id)
        if not doc:
            return [chunk]

        # Find chunk index in document
        try:
            chunk_idx = next(
                i for i, c in enumerate(doc.chunks)
                if c.chunk_id == chunk.chunk_id
            )
        except StopIteration:
            return [chunk]

        # Get context window
        start_idx = max(0, chunk_idx - context_chunks)
        end_idx = min(len(doc.chunks), chunk_idx + context_chunks + 1)

        return doc.chunks[start_idx:end_idx]

    def save_index(self, save_dir: Path) -> None:
        """
        Save BM25 index and metadata to disk

        Note: BM25Okapi doesn't have built-in serialization,
        so we save the tokenized corpus and rebuild on load
        """
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        # Save tokenized corpus
        corpus_file = save_dir / "bm25_corpus.json"
        with open(corpus_file, 'w', encoding='utf-8') as f:
            json.dump(self.tokenized_corpus, f)

        logger.info(f"BM25 index metadata saved to {save_dir}")

    def load_index(self, load_dir: Path, documents: List[StructuredDocument]) -> None:
        """
        Load BM25 index from disk

        Args:
            load_dir: Directory containing saved index
            documents: Documents to index (needed for full rebuild)
        """
        load_dir = Path(load_dir)
        corpus_file = load_dir / "bm25_corpus.json"

        if corpus_file.exists():
            with open(corpus_file, 'r', encoding='utf-8') as f:
                self.tokenized_corpus = json.load(f)

            # Rebuild from documents (ensures chunks are available)
            self.build_index(documents)
            logger.info(f"BM25 index loaded from {load_dir}")
        else:
            logger.warning(f"BM25 index file not found: {corpus_file}")
            self.build_index(documents)

    def get_stats(self) -> Dict[str, any]:
        """Get search engine statistics"""
        return {
            "total_chunks": len(self.chunks),
            "total_documents": len(self.documents),
            "corpus_size": len(self.tokenized_corpus),
            "avg_tokens_per_chunk": (
                sum(len(tokens) for tokens in self.tokenized_corpus) / len(self.tokenized_corpus)
                if self.tokenized_corpus else 0
            )
        }
