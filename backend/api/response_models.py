"""
API Response Models - Lightweight versions for frontend
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from backend.models.knowledge_schema import DocType, Jurisdiction, DocumentVersion


class DocumentMetadata(BaseModel):
    """Lightweight document metadata for API responses"""
    doc_id: str
    title: str
    file_path: str
    doctype: DocType
    jurisdiction: Jurisdiction
    parties: List[str] = Field(default_factory=list)
    effective_date: Optional[datetime] = None
    version: DocumentVersion = DocumentVersion.DRAFT
    total_pages: int


class ChunkMetadata(BaseModel):
    """Lightweight chunk metadata for API responses"""
    chunk_id: str
    text: str
    section_path: List[str] = Field(default_factory=list)
    section_title: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    is_header: bool = False
    is_definition: bool = False
    contains_dates: bool = False
    contains_money: bool = False


class SearchResultResponse(BaseModel):
    """Search result for API response"""
    chunk: ChunkMetadata
    document: DocumentMetadata

    # Scoring
    bm25_score: float = 0.0
    vector_score: float = 0.0
    metadata_boost: float = 0.0
    final_score: float = 0.0

    # Highlights
    match_highlights: List[str] = Field(default_factory=list)


class QueryResponseAPI(BaseModel):
    """Query response for API"""
    original_query: str
    results: List[SearchResultResponse]
    total_found: int

    # AI Summary
    summary: str
    confidence: float

    # Legal disclaimer
    disclaimer: str

    # Performance
    search_time_ms: float
    generation_time_ms: float
    total_time_ms: float


def convert_to_api_response(internal_response) -> QueryResponseAPI:
    """
    Convert internal QueryResponse to lightweight API response

    Args:
        internal_response: QueryResponse from knowledge_schema

    Returns:
        QueryResponseAPI with lightweight models
    """
    from backend.models.knowledge_schema import SearchResult, QueryResponse

    results = []
    for result in internal_response.results:
        # Extract only needed chunk metadata
        chunk_meta = ChunkMetadata(
            chunk_id=result.chunk.chunk_id,
            text=result.chunk.text,
            section_path=result.chunk.section_path,
            section_title=result.chunk.section_title,
            page_start=result.chunk.page_start,
            page_end=result.chunk.page_end,
            is_header=result.chunk.is_header,
            is_definition=result.chunk.is_definition,
            contains_dates=result.chunk.contains_dates,
            contains_money=result.chunk.contains_money
        )

        # Extract only needed document metadata
        doc_meta = DocumentMetadata(
            doc_id=result.document.doc_id,
            title=result.document.title,
            file_path=result.document.file_path,
            doctype=result.document.doctype,
            jurisdiction=result.document.jurisdiction,
            parties=result.document.parties,
            effective_date=result.document.effective_date,
            version=result.document.version,
            total_pages=result.document.total_pages
        )

        # Create lightweight search result
        api_result = SearchResultResponse(
            chunk=chunk_meta,
            document=doc_meta,
            bm25_score=result.bm25_score,
            vector_score=result.vector_score,
            metadata_boost=result.metadata_boost,
            final_score=result.final_score,
            match_highlights=result.match_highlights
        )

        results.append(api_result)

    # Create API response
    return QueryResponseAPI(
        original_query=internal_response.original_query,
        results=results,
        total_found=internal_response.total_found,
        summary=internal_response.summary,
        confidence=internal_response.confidence,
        disclaimer=internal_response.disclaimer,
        search_time_ms=internal_response.search_time_ms,
        generation_time_ms=internal_response.generation_time_ms,
        total_time_ms=internal_response.total_time_ms
    )
