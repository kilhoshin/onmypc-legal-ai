"""
API request/response schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Search query request"""
    query: str = Field(..., min_length=1, max_length=1000)
    stream: bool = Field(default=False)


class EULAAcceptRequest(BaseModel):
    """EULA acceptance request"""
    accepted: bool


class IndexingRequest(BaseModel):
    """Document indexing request"""
    doc_dir: Optional[str] = None


class StatusResponse(BaseModel):
    """System status response"""
    status: str
    eula_accepted: bool
    total_documents: int
    total_chunks: int
    knowledge_base_loaded: bool = False  # Whether existing KB was auto-loaded
