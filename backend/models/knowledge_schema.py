"""
Structured Knowledge Schema for Legal Documents
Advanced metadata-rich document representation
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DocType(str, Enum):
    """Standard document types"""
    CONTRACT = "contract"
    NDA = "nda"
    POLICY = "policy"
    AGREEMENT = "agreement"
    LICENSE = "license"
    MEMO = "memo"
    BRIEF = "brief"
    OPINION = "opinion"
    REGULATION = "regulation"
    STATUTE = "statute"
    CASE_LAW = "case_law"
    OTHER = "other"


class Jurisdiction(str, Enum):
    """US Jurisdictions"""
    FEDERAL = "US"
    CALIFORNIA = "CA"
    NEW_YORK = "NY"
    TEXAS = "TX"
    FLORIDA = "FL"
    ILLINOIS = "IL"
    # Add more as needed
    OTHER = "OTHER"


class DocumentVersion(str, Enum):
    """Document status/version"""
    DRAFT = "draft"
    REDLINE = "redline"
    SIGNED = "signed"
    EXECUTED = "executed"
    ARCHIVED = "archived"


class SectionNode(BaseModel):
    """Hierarchical section structure"""
    id: str
    number: Optional[str] = None  # e.g., "5.2"
    title: str
    level: int  # 0=root, 1=chapter, 2=section, 3=subsection
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    text_start_idx: Optional[int] = None
    text_end_idx: Optional[int] = None


class EnrichedChunk(BaseModel):
    """
    Enhanced document chunk with full metadata
    """
    # Core IDs
    chunk_id: str  # Format: {doc_id}#p{page}#c{chunk_num}
    doc_id: str

    # Content
    text: str
    tokens: int

    # Location
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None

    # Section context
    section_id: Optional[str] = None
    section_path: List[str] = Field(default_factory=list)  # ["Agreement", "§5", "§5.2"]
    section_title: Optional[str] = None

    # Vector representation
    embedding_vector: Optional[List[float]] = None

    # Metadata
    meta: Dict[str, Any] = Field(default_factory=dict)

    # Text features (for BM25)
    term_frequencies: Optional[Dict[str, int]] = None

    # Importance scores
    is_header: bool = False
    is_definition: bool = False
    contains_dates: bool = False
    contains_money: bool = False
    contains_parties: bool = False

    class Config:
        arbitrary_types_allowed = True


class StructuredDocument(BaseModel):
    """
    Complete structured document representation
    """
    # Core identification
    doc_id: str
    title: str
    file_path: str
    file_hash: str  # SHA-256 for version detection
    source_folder: Optional[str] = None  # Root folder where this document was indexed from

    # Classification
    doctype: DocType
    doctype_confidence: float = 0.0

    # Jurisdiction
    jurisdiction: Jurisdiction
    jurisdiction_confidence: float = 0.0

    # Parties (if applicable)
    parties: List[str] = Field(default_factory=list)

    # Dates
    creation_date: Optional[datetime] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    indexed_at: datetime

    # Version control
    version: DocumentVersion = DocumentVersion.DRAFT
    version_number: Optional[str] = None

    # Structure
    total_pages: int
    total_sections: int
    section_tree: List[SectionNode] = Field(default_factory=list)

    # Chunks
    chunks: List[EnrichedChunk] = Field(default_factory=list)
    total_chunks: int = 0

    # Full text (for BM25)
    full_text: Optional[str] = None

    # Key extractions
    defined_terms: Dict[str, str] = Field(default_factory=dict)  # term -> definition
    key_clauses: List[str] = Field(default_factory=list)  # Important clause types found

    # Access control
    acl: List[str] = Field(default_factory=lambda: ["all"])

    # Custom metadata
    custom_meta: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class SearchQuery(BaseModel):
    """
    Structured search query from LLM agent
    """
    # Original user query
    raw_query: str

    # Interpreted query
    intent: str  # e.g., "find_clause", "check_enforceability", "compare_terms"
    entities: Dict[str, List[str]] = Field(default_factory=dict)  # {"clause_type": ["non-compete"], ...}

    # Filters
    doctypes: Optional[List[DocType]] = None
    jurisdictions: Optional[List[Jurisdiction]] = None
    date_range: Optional[tuple] = None
    parties: Optional[List[str]] = None

    # Search params
    text_query: str  # Processed query for search
    required_terms: List[str] = Field(default_factory=list)
    excluded_terms: List[str] = Field(default_factory=list)

    # Ranking preferences
    boost_recent: bool = True
    boost_headers: bool = True
    boost_signed_docs: bool = True

    # Result preferences
    top_k: int = 5
    include_context: bool = True

    class Config:
        arbitrary_types_allowed = True


class SearchResult(BaseModel):
    """
    Enhanced search result with multiple scores
    """
    chunk: EnrichedChunk
    document: StructuredDocument

    # Multi-faceted scoring
    bm25_score: float = 0.0
    vector_score: float = 0.0
    cross_encoder_score: Optional[float] = None

    # Metadata boosts
    metadata_boost: float = 0.0
    final_score: float = 0.0

    # Explanation
    match_highlights: List[str] = Field(default_factory=list)
    explanation: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class QueryResponse(BaseModel):
    """
    Complete query response with agent interaction
    """
    original_query: str
    structured_query: SearchQuery

    results: List[SearchResult]
    total_found: int

    # Agent response
    summary: str
    confidence: float

    # Citations
    cited_chunks: List[str] = Field(default_factory=list)

    # Legal disclaimer
    disclaimer: str

    # Performance metrics
    search_time_ms: float
    generation_time_ms: float
    total_time_ms: float
