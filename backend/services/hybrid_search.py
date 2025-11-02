"""
Hybrid Search Engine
Combines BM25 (keyword) + Vector (semantic) + Cross-Encoder (reranking)
"""
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging
import numpy as np
from collections import defaultdict

from backend.models.knowledge_schema import (
    StructuredDocument,
    EnrichedChunk,
    SearchQuery,
    SearchResult,
    DocumentVersion
)
from backend.services.bm25_search import BM25SearchEngine

logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """
    Multi-stage hybrid search engine

    Pipeline:
    1. BM25 keyword search (fast, high recall)
    2. Vector semantic search (understanding, synonyms)
    3. Result fusion with RRF (Reciprocal Rank Fusion)
    4. Metadata boosting (document type, date, version, section type)
    5. Cross-encoder reranking (precise relevance)

    This approach maximizes both recall (finding relevant docs) and
    precision (ranking them correctly).
    """

    def __init__(
        self,
        bm25_engine: BM25SearchEngine,
        vector_search_engine,  # Typically backend.services.knowledge_indexer.KnowledgeIndexer
        cross_encoder_model=None  # Optional: load cross-encoder for reranking
    ):
        self.bm25_engine = bm25_engine
        self.vector_engine = vector_search_engine
        self.cross_encoder = cross_encoder_model

        # Fusion weights
        self.bm25_weight = 0.4  # Keyword matching
        self.vector_weight = 0.6  # Semantic understanding

        # Metadata boost factors
        self.boost_factors = {
            "is_header": 1.3,
            "is_definition": 1.2,
            "contains_dates": 1.1,
            "contains_money": 1.1,
            "signed_doc": 1.3,
            "recent_doc": 1.2,
        }

    def search(
        self,
        structured_query: SearchQuery,
        score_threshold: float = 0.3,  # Minimum relevance threshold (normalized 0-1)
        min_results: int = 3,           # Minimum results to return
        max_results: int = 10,          # Maximum results to return
        strict_threshold: bool = False  # When True, never include below-threshold results
    ) -> List[SearchResult]:
        """
        Perform hybrid search with full pipeline

        Args:
            structured_query: Structured query with filters and preferences
            score_threshold: Minimum final_score to include (default: 0.01)
            min_results: Minimum number of results (default: 3)
            max_results: Maximum number of results (default: 10)

        Returns:
            List of SearchResult objects with multi-faceted scoring
        """
        logger.info(f"Hybrid search for: {structured_query.raw_query}")
        logger.info(f"Intent: {structured_query.intent}")
        logger.info(f"Filters: threshold={score_threshold}, min={min_results}, max={max_results}")

        # Stage 1: BM25 keyword search
        bm25_results = self.bm25_engine.search_with_filters(structured_query)
        logger.info(f"BM25 returned {len(bm25_results)} results")

        # Stage 2: Vector semantic search
        vector_results = self._vector_search_with_filters(structured_query)
        logger.info(f"Vector search returned {len(vector_results)} results")

        # Stage 3: Fuse results using Reciprocal Rank Fusion (RRF)
        fused_results = self._reciprocal_rank_fusion(
            bm25_results=bm25_results,
            vector_results=vector_results,
            k=60  # RRF parameter
        )
        logger.info(f"Fused {len(fused_results)} unique results")

        # Stage 4: Apply metadata boosting
        boosted_results = self._apply_metadata_boosting(
            results=fused_results,
            query=structured_query
        )

        # Stage 5: Cross-encoder reranking (optional, for top-k)
        if self.cross_encoder and len(boosted_results) > 0:
            top_k_for_rerank = min(20, len(boosted_results))
            reranked_results = self._cross_encoder_rerank(
                query=structured_query.text_query,
                results=boosted_results[:top_k_for_rerank]
            )
            # Combine reranked top-k with rest
            final_results = reranked_results + boosted_results[top_k_for_rerank:]
        else:
            final_results = boosted_results

        # Normalize scores to 0-1 range (max score = 1.0)
        if final_results:
            max_score = final_results[0][4]  # Highest final_score
            if max_score > 0:
                normalized_results = [
                    (chunk, bm25, vec, boost, score / max_score)
                    for chunk, bm25, vec, boost, score in final_results
                ]
            else:
                normalized_results = final_results
        else:
            normalized_results = []

        # Convert to SearchResult objects with threshold filtering
        search_results = []
        above_threshold = []
        below_threshold = []

        for chunk, bm25_score, vector_score, metadata_boost, final_score in normalized_results:
            doc = self.bm25_engine.get_document(chunk.doc_id)
            if not doc:
                continue

            search_result = SearchResult(
                chunk=chunk,
                document=doc,
                bm25_score=bm25_score,
                vector_score=vector_score,
                metadata_boost=metadata_boost,
                final_score=final_score,
                match_highlights=self._extract_highlights(chunk, structured_query)
            )

            if final_score >= score_threshold:
                above_threshold.append(search_result)
            else:
                below_threshold.append(search_result)

        if strict_threshold:
            search_results = above_threshold[:max_results]
        else:
            # Apply smart filtering:
            # 1. If we have enough above threshold, use those (up to max)
            # 2. If below min, add from below threshold to reach min
            # 3. Never exceed max
            if len(above_threshold) >= min_results:
                search_results = above_threshold[:max_results]
            else:
                # Need to add some below threshold to reach min
                needed = min(min_results - len(above_threshold), len(below_threshold))
                search_results = above_threshold + below_threshold[:needed]
                search_results = search_results[:max_results]

        logger.info(
            f"Returning {len(search_results)} results "
            f"({len(above_threshold)} above threshold {score_threshold:.3f}, strict={strict_threshold})"
        )
        return search_results

    def _vector_search_with_filters(
        self,
        query: SearchQuery
    ) -> List[Tuple[EnrichedChunk, float]]:
        """
        Perform vector search with metadata filters

        Note: This wraps the existing vector search from knowledge_indexer
        and applies the same filters as BM25 search
        """
        # Get candidate doc IDs from filters
        candidate_doc_ids = self.bm25_engine._apply_filters(query)

        # Perform vector search using knowledge_indexer
        try:
            results = self.vector_engine.vector_search(
                query_text=query.text_query,
                top_k=query.top_k * 2,  # Get more for fusion
                filter_doc_ids=candidate_doc_ids
            )
            return results
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []

    def _reciprocal_rank_fusion(
        self,
        bm25_results: List[Tuple[EnrichedChunk, float]],
        vector_results: List[Tuple[EnrichedChunk, float]],
        k: int = 60
    ) -> List[Tuple[EnrichedChunk, float, float, float, float]]:
        """
        Fuse BM25 and vector results using weighted score combination

        Instead of pure RRF (which only uses ranks), we:
        1. Normalize BM25 and vector scores to 0-1 range
        2. Combine with weighted average
        3. This preserves actual score magnitudes (better relevance distinction)

        Returns:
            List of (chunk, bm25_score, vector_score, metadata_boost=0, final_score)
        """
        # Normalize BM25 scores to 0-1
        if bm25_results:
            max_bm25 = max(score for _, score in bm25_results)
            bm25_normalized = {
                chunk.chunk_id: (chunk, score / max_bm25 if max_bm25 > 0 else 0.0)
                for chunk, score in bm25_results
            }
        else:
            bm25_normalized = {}

        # Normalize Vector scores to 0-1
        if vector_results:
            max_vector = max(score for _, score in vector_results)
            vector_normalized = {
                chunk.chunk_id: (chunk, score / max_vector if max_vector > 0 else 0.0)
                for chunk, score in vector_results
            }
        else:
            vector_normalized = {}

        # Get all unique chunks
        all_chunk_ids = set(bm25_normalized.keys()) | set(vector_normalized.keys())

        # Combine scores with weighted average
        fused = []
        chunk_map = {}

        # Build chunk lookup
        for chunk_id in all_chunk_ids:
            if chunk_id in bm25_normalized:
                chunk_map[chunk_id] = bm25_normalized[chunk_id][0]
            elif chunk_id in vector_normalized:
                chunk_map[chunk_id] = vector_normalized[chunk_id][0]

        for chunk_id in all_chunk_ids:
            chunk = chunk_map[chunk_id]

            # Get normalized scores (0 if not present)
            bm25_score = bm25_normalized.get(chunk_id, (None, 0.0))[1]
            vector_score = vector_normalized.get(chunk_id, (None, 0.0))[1]

            # Weighted combination (preserves score magnitudes)
            combined_score = self.bm25_weight * bm25_score + self.vector_weight * vector_score

            fused.append((
                chunk,
                float(bm25_score),
                float(vector_score),
                0.0,  # metadata_boost (applied later)
                combined_score  # initial final_score
            ))

        # Sort by combined score
        fused.sort(key=lambda x: x[4], reverse=True)

        return fused

    def _apply_metadata_boosting(
        self,
        results: List[Tuple[EnrichedChunk, float, float, float, float]],
        query: SearchQuery
    ) -> List[Tuple[EnrichedChunk, float, float, float, float]]:
        """
        Apply metadata-based score boosting

        Boosts:
        - Headers and definitions (if boost_headers enabled)
        - Recent documents (if boost_recent enabled)
        - Signed/executed documents (if boost_signed_docs enabled)
        - Chunks with dates/money (for financial queries)
        """
        boosted = []

        for chunk, bm25_score, vector_score, _, base_score in results:
            boost = 1.0

            # Boost headers
            if query.boost_headers and chunk.is_header:
                boost *= self.boost_factors["is_header"]

            # Boost definitions
            if chunk.is_definition:
                boost *= self.boost_factors["is_definition"]

            # Boost chunks with dates/money (context-dependent)
            if chunk.contains_dates and ("date" in query.text_query.lower() or "when" in query.text_query.lower()):
                boost *= self.boost_factors["contains_dates"]
            if chunk.contains_money and ("$" in query.text_query or "pay" in query.text_query.lower()):
                boost *= self.boost_factors["contains_money"]

            # Document-level boosts
            doc = self.bm25_engine.get_document(chunk.doc_id)
            if doc:
                # Boost signed/executed documents
                if query.boost_signed_docs and doc.version in [DocumentVersion.SIGNED, DocumentVersion.EXECUTED]:
                    boost *= self.boost_factors["signed_doc"]

                # Boost recent documents
                if query.boost_recent and doc.effective_date:
                    days_old = (datetime.now() - doc.effective_date).days
                    if days_old < 365:  # Less than 1 year old
                        boost *= self.boost_factors["recent_doc"]

            # Calculate final score
            final_score = base_score * boost
            metadata_boost = boost

            boosted.append((chunk, bm25_score, vector_score, metadata_boost, final_score))

        # Re-sort by final score
        boosted.sort(key=lambda x: x[4], reverse=True)

        return boosted

    def _cross_encoder_rerank(
        self,
        query: str,
        results: List[Tuple[EnrichedChunk, float, float, float, float]]
    ) -> List[Tuple[EnrichedChunk, float, float, float, float]]:
        """
        Rerank top results using cross-encoder

        Cross-encoders jointly encode query and document,
        providing more accurate relevance scores than bi-encoders.

        Note: This is computationally expensive, so only apply to top-k.
        """
        if not self.cross_encoder:
            return results

        logger.info(f"Cross-encoder reranking {len(results)} results")

        # Prepare pairs for cross-encoder
        pairs = [(query, chunk.text) for chunk, *_ in results]

        # Get cross-encoder scores
        try:
            # Assuming cross-encoder is sentence-transformers CrossEncoder
            ce_scores = self.cross_encoder.predict(pairs)
        except Exception as e:
            logger.error(f"Cross-encoder failed: {e}")
            return results

        # Update final scores with cross-encoder
        reranked = []
        for idx, (chunk, bm25_score, vector_score, metadata_boost, base_score) in enumerate(results):
            ce_score = float(ce_scores[idx])

            # Combine: weighted average of RRF score and cross-encoder score
            final_score = 0.7 * ce_score + 0.3 * base_score

            reranked.append((chunk, bm25_score, vector_score, metadata_boost, final_score))

        # Sort by new final score
        reranked.sort(key=lambda x: x[4], reverse=True)

        logger.info("Cross-encoder reranking complete")
        return reranked

    def _extract_highlights(
        self,
        chunk: EnrichedChunk,
        query: SearchQuery
    ) -> List[str]:
        """
        Extract highlighted snippets showing query match

        Returns list of text snippets with matched terms in context
        """
        query_tokens = set(self.bm25_engine.tokenize(query.text_query))
        chunk_tokens = self.bm25_engine.tokenize(chunk.text)

        # Find matching tokens
        matches = query_tokens & set(chunk_tokens)

        if not matches:
            # Return first 200 chars as fallback
            return [chunk.text[:200] + "..."]

        # Find sentences with matches
        sentences = chunk.text.split('. ')
        highlights = []

        for sentence in sentences:
            sentence_tokens = set(self.bm25_engine.tokenize(sentence))
            if sentence_tokens & matches:
                highlights.append(sentence.strip())
                if len(highlights) >= 3:
                    break

        return highlights if highlights else [chunk.text[:200] + "..."]

    def get_stats(self) -> Dict[str, any]:
        """Get search engine statistics"""
        return {
            "bm25_stats": self.bm25_engine.get_stats(),
            "vector_stats": {},  # TODO: Add vector engine stats
            "fusion_weights": {
                "bm25": self.bm25_weight,
                "vector": self.vector_weight
            },
            "boost_factors": self.boost_factors
        }
