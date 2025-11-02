"""
Query Agent
Transforms natural language queries into structured search queries and assembles responses
"""
from typing import List, Dict, Optional
import re
import logging
from datetime import datetime

from backend.models.knowledge_schema import (
    SearchQuery,
    SearchResult,
    QueryResponse,
    DocType,
    Jurisdiction
)
from backend.config import settings
logger = logging.getLogger(__name__)


class QueryAgent:
    """
    Agent for query understanding and response assembly

    Responsibilities:
    1. Intent classification (find_clause, check_compliance, etc.)
    2. Entity extraction (parties, dates, jurisdictions, etc.)
    3. Query structuring (filters, boosts, parameters)
    4. Response packaging (confidence, timing metadata)
    """

    # Intent patterns
    INTENT_PATTERNS = {
        "find_clause": [
            r"find.*clause", r"show.*clause", r"what.*clause",
            r"non-compete", r"termination", r"confidentiality",
            r"liability", r"indemnification", r"arbitration"
        ],
        "check_compliance": [
            r"compli\w+", r"legal", r"violat\w+", r"require\w+"
        ],
        "compare_terms": [
            r"compar\w+", r"difference", r"similar", r"contrast"
        ],
        "find_definition": [
            r"what is", r"define", r"definition", r"means", r"refers to"
        ],
        "extract_dates": [
            r"when", r"date", r"deadline", r"expire", r"effective"
        ],
        "extract_parties": [
            r"who", r"parties", r"party", r"between.*and"
        ],
        "summarize": [
            r"summar\w+", r"overview", r"explain", r"describe"
        ]
    }

    # Entity extraction patterns
    CLAUSE_TYPES = [
        "non-compete", "non-disclosure", "confidentiality",
        "termination", "liability", "indemnification",
        "arbitration", "governing law", "force majeure",
        "intellectual property", "warranty", "payment"
    ]

    JURISDICTION_MAP = {
        "california": Jurisdiction.CALIFORNIA,
        "ca": Jurisdiction.CALIFORNIA,
        "new york": Jurisdiction.NEW_YORK,
        "ny": Jurisdiction.NEW_YORK,
        "texas": Jurisdiction.TEXAS,
        "tx": Jurisdiction.TEXAS,
        "florida": Jurisdiction.FLORIDA,
        "fl": Jurisdiction.FLORIDA,
        "illinois": Jurisdiction.ILLINOIS,
        "il": Jurisdiction.ILLINOIS,
        "federal": Jurisdiction.FEDERAL,
        "us": Jurisdiction.FEDERAL,
    }

    DOCTYPE_MAP = {
        "contract": DocType.CONTRACT,
        "agreement": DocType.AGREEMENT,
        "nda": DocType.NDA,
        "non-disclosure": DocType.NDA,
        "policy": DocType.POLICY,
        "license": DocType.LICENSE,
        "memo": DocType.MEMO,
        "memorandum": DocType.MEMO,
        "brief": DocType.BRIEF,
        "opinion": DocType.OPINION,
        "regulation": DocType.REGULATION,
        "statute": DocType.STATUTE,
        "case law": DocType.CASE_LAW,
    }

    def __init__(self):
        """Initialize query agent without external LLM dependencies."""
        self.disclaimer = settings.DISCLAIMER_TEXT

    def parse_query(self, raw_query: str) -> SearchQuery:
        """
        Parse natural language query into structured SearchQuery

        Uses rule-based extraction.

        Args:
            raw_query: User's natural language query

        Returns:
            Structured SearchQuery object
        """
        logger.info(f"Parsing query: {raw_query}")

        query_lower = raw_query.lower()

        # 1. Classify intent
        intent = self._classify_intent(query_lower)
        logger.info(f"Detected intent: {intent}")

        # 2. Extract entities
        entities = self._extract_entities(query_lower)
        logger.info(f"Extracted entities: {entities}")

        # 3. Extract filters
        doctypes = self._extract_doctypes(query_lower)
        jurisdictions = self._extract_jurisdictions(query_lower)

        # 4. Build text query (processed for search)
        text_query = self._build_text_query(raw_query, entities)

        # 5. Extract required/excluded terms
        required_terms = self._extract_required_terms(query_lower)
        excluded_terms = self._extract_excluded_terms(query_lower)

        # 6. Determine ranking preferences
        boost_recent = "recent" in query_lower or "latest" in query_lower
        boost_headers = intent in ["find_clause", "find_definition"]
        boost_signed = "signed" in query_lower or "executed" in query_lower

        # 7. Create structured query
        structured_query = SearchQuery(
            raw_query=raw_query,
            intent=intent,
            entities=entities,
            doctypes=doctypes if doctypes else None,
            jurisdictions=jurisdictions if jurisdictions else None,
            text_query=text_query,
            required_terms=required_terms,
            excluded_terms=excluded_terms,
            boost_recent=boost_recent,
            boost_headers=boost_headers,
            boost_signed_docs=boost_signed,
            top_k=10,
            include_context=True
        )

        return structured_query

    def _classify_intent(self, query: str) -> str:
        """
        Classify query intent using pattern matching

        Returns intent string (e.g., "find_clause")
        """
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return intent

        return "general_search"  # Default

    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extract named entities from query

        Returns dict with entity types and values
        """
        entities = {}

        # Extract clause types
        clause_types = []
        for clause_type in self.CLAUSE_TYPES:
            if clause_type in query:
                clause_types.append(clause_type)
        if clause_types:
            entities["clause_type"] = clause_types

        # Extract dates (simple patterns)
        date_patterns = [
            r'\b(19|20)\d{2}\b',  # Years
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b'
        ]
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                # Check if matches are strings or tuples
                if isinstance(matches[0], str):
                    dates.extend(matches)
                else:
                    # Extract first element from tuples
                    dates.extend([m[0] if isinstance(m, tuple) else m for m in matches])
        if dates:
            entities["dates"] = dates

        # Extract party names (after "between", "with", "party")
        party_pattern = r'\b(?:between|with|party)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        party_matches = re.findall(party_pattern, query)
        if party_matches:
            entities["parties"] = party_matches

        return entities

    def _extract_doctypes(self, query: str) -> Optional[List[DocType]]:
        """Extract document type filters from query"""
        doctypes = []
        for keyword, doctype in self.DOCTYPE_MAP.items():
            if keyword in query:
                if doctype not in doctypes:
                    doctypes.append(doctype)
        return doctypes if doctypes else None

    def _extract_jurisdictions(self, query: str) -> Optional[List[Jurisdiction]]:
        """Extract jurisdiction filters from query"""
        jurisdictions = []
        for keyword, jurisdiction in self.JURISDICTION_MAP.items():
            if re.search(r'\b' + keyword + r'\b', query, re.IGNORECASE):
                if jurisdiction not in jurisdictions:
                    jurisdictions.append(jurisdiction)
        return jurisdictions if jurisdictions else None

    def _build_text_query(self, raw_query: str, entities: Dict[str, List[str]]) -> str:
        """
        Build processed text query for search

        Enhances query with extracted entities
        """
        # Start with raw query
        text_query = raw_query

        # Add clause types as search terms
        if "clause_type" in entities:
            text_query += " " + " ".join(entities["clause_type"])

        return text_query

    def _extract_required_terms(self, query: str) -> List[str]:
        """
        Extract terms that MUST appear (using quotes or + prefix)

        Examples: "non-compete clause", +california
        """
        required = []

        # Quoted phrases
        quoted = re.findall(r'"([^"]+)"', query)
        required.extend(quoted)

        # + prefix
        plus_terms = re.findall(r'\+(\w+)', query)
        required.extend(plus_terms)

        return required

    def _extract_excluded_terms(self, query: str) -> List[str]:
        """
        Extract terms that must NOT appear (using - prefix)

        Example: -draft (exclude draft documents)
        """
        excluded = re.findall(r'-(\w+)', query)
        return excluded

    def generate_response(
        self,
        query: SearchQuery,
        results: List[SearchResult],
        search_time_ms: float,
    ) -> QueryResponse:
        """
        Assemble query response payload from search results

        Args:
            query: Structured query
            results: Search results
            search_time_ms: Search execution time

        Returns:
            Complete QueryResponse without LLM summary
        """
        logger.info(f"Generating response for {len(results)} results")

        start_time = datetime.now()

        # Basic metadata
        cited_chunks = [r.chunk.chunk_id for r in results[:5]] if results else []
        confidence = self._calculate_confidence(results)

        generation_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Build response
        response = QueryResponse(
            original_query=query.raw_query,
            structured_query=query,
            results=results,
            total_found=len(results),
            summary="",
            confidence=confidence,
            cited_chunks=cited_chunks,
            disclaimer=self.disclaimer,
            search_time_ms=search_time_ms,
            generation_time_ms=generation_time_ms,
            total_time_ms=search_time_ms + generation_time_ms
        )

        return response

    def _calculate_confidence(self, results: List[SearchResult]) -> float:
        """
        Calculate confidence score based on result quality

        Factors:
        - Number of results
        - Score distribution
        - Cross-encoder scores if available
        """
        if not results:
            return 0.0

        top_score = results[0].final_score
        avg_score = sum(r.final_score for r in results) / len(results)

        # High confidence if:
        # - Top score is high
        # - Multiple results with good scores
        # - Top score significantly higher than average
        confidence = min(1.0, top_score * 0.5 + (top_score - avg_score) * 0.3 + min(len(results) / 5, 1.0) * 0.2)

        return round(confidence, 2)
