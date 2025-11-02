"""
API routes - Updated for new architecture
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from backend.api.schemas import (
    QueryRequest,
    EULAAcceptRequest,
    IndexingRequest,
    StatusResponse
)
from backend.api.response_models import QueryResponseAPI, convert_to_api_response
from backend.config import settings
from backend.services.security import EULAService
from backend.services.legal_ai_service import LegalAIService
from backend.utils.logger import setup_logger, AuditLogger

logger = setup_logger(__name__)

# Initialize services (will be set in main.py)
legal_ai_service: LegalAIService = None
eula_service: EULAService = None
audit_logger: AuditLogger = None

router = APIRouter()


def init_services(
    ai_svc: LegalAIService,
    eula_svc: EULAService,
    audit_log: AuditLogger
):
    """Initialize services"""
    global legal_ai_service, eula_service, audit_logger
    legal_ai_service = ai_svc
    eula_service = eula_svc
    audit_logger = audit_log


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get system status"""
    # Check if service is ready
    stats = legal_ai_service.get_stats()

    # Get document counts
    indexer_stats = stats.get("indexer", {})
    total_documents = indexer_stats.get("total_documents", 0)
    total_chunks = indexer_stats.get("total_chunks", 0)

    return StatusResponse(
        status="ready" if (eula_service.is_eula_accepted() and stats["is_ready"]) else "awaiting_eula",
        eula_accepted=eula_service.is_eula_accepted(),
        total_documents=total_documents,
        total_chunks=total_chunks,
        knowledge_base_loaded=(total_documents > 0 and stats["is_ready"])
    )


@router.get("/eula")
async def get_eula():
    """Get EULA text"""
    return {
        "version": settings.EULA_VERSION,
        "text": eula_service.get_eula_text(),
        "accepted": eula_service.is_eula_accepted()
    }


@router.post("/eula/accept")
async def accept_eula(request: EULAAcceptRequest):
    """Accept EULA"""
    if not request.accepted:
        raise HTTPException(status_code=400, detail="EULA must be accepted")

    success = eula_service.accept_eula()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to save EULA acceptance")

    audit_logger.log_event("eula_accepted", {"version": settings.EULA_VERSION})

    return {"status": "accepted", "version": settings.EULA_VERSION}


@router.post("/index")
async def start_indexing(
    request: IndexingRequest,
    background_tasks: BackgroundTasks
):
    """Start document indexing"""
    if not eula_service.is_eula_accepted():
        raise HTTPException(status_code=403, detail="EULA must be accepted first")

    logger.info(f"Received indexing request: doc_dir={request.doc_dir}")

    doc_dir = Path(request.doc_dir) if request.doc_dir else settings.DOCS_DIR

    logger.info(f"Using directory: {doc_dir}")

    if not doc_dir.exists():
        logger.error(f"Directory does not exist: {doc_dir}")
        raise HTTPException(status_code=404, detail=f"Directory not found: {doc_dir}")

    # Run indexing in background
    background_tasks.add_task(
        _run_indexing,
        doc_dir
    )

    return {
        "status": "indexing_started",
        "doc_dir": str(doc_dir)
    }


def _run_indexing(doc_dir: Path):
    """Background task for indexing"""
    try:
        logger.info(f"Starting indexing: {doc_dir}")
        result = legal_ai_service.index_documents(doc_dir)

        if result.get("status") == "success":
            audit_logger.log_indexing(
                result.get("indexed_documents", 0),
                result.get("indexing_time_seconds", 0)
            )

            logger.info(
                f"Indexing completed: {result.get('indexed_documents', 0)} documents, "
                f"{result.get('indexing_time_seconds', 0)}s"
            )
        else:
            logger.error(f"Indexing failed: {result.get('message', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Indexing failed: {e}")


@router.get("/index/stats")
async def get_index_stats():
    """Get indexing statistics"""
    if not eula_service.is_eula_accepted():
        raise HTTPException(status_code=403, detail="EULA must be accepted first")

    stats = legal_ai_service.get_stats()

    # Flatten for frontend compatibility
    indexer_stats = stats.get("indexer", {})
    return {
        "total_documents": indexer_stats.get("total_documents", 0),
        "total_chunks": indexer_stats.get("total_chunks", 0),
        "faiss_vectors": indexer_stats.get("faiss_vectors", 0),
        "is_ready": stats.get("is_ready", False),
    }


@router.get("/documents")
async def get_documents():
    """Get list of indexed documents"""
    if not eula_service.is_eula_accepted():
        raise HTTPException(status_code=403, detail="EULA must be accepted first")

    return {
        "documents": legal_ai_service.get_document_list()
    }


@router.get("/documents/{doc_id}")
async def get_document_details(doc_id: str):
    """Get detailed information about a document"""
    if not eula_service.is_eula_accepted():
        raise HTTPException(status_code=403, detail="EULA must be accepted first")

    doc = legal_ai_service.get_document_details(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return doc


@router.get("/folders")
async def get_indexed_folders():
    """Get list of indexed document folders"""
    if not eula_service.is_eula_accepted():
        raise HTTPException(status_code=403, detail="EULA must be accepted first")

    return {
        "folders": legal_ai_service.folder_manager.get_folders()
    }


@router.delete("/folders/{folder_path:path}")
async def remove_indexed_folder(folder_path: str):
    """Remove a folder from the indexed list"""
    if not eula_service.is_eula_accepted():
        raise HTTPException(status_code=403, detail="EULA must be accepted first")

    result = legal_ai_service.remove_indexed_folder(folder_path)
    if result.get("status") == "removed":
        return result
    else:
        raise HTTPException(status_code=404, detail="Folder not found")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return legal_ai_service.health_check()


@router.post("/query", response_model=QueryResponseAPI)
async def query(request: QueryRequest):
    """Process search query"""
    if not eula_service.is_eula_accepted():
        raise HTTPException(status_code=403, detail="EULA must be accepted first")

    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="Use /query/stream for streaming responses"
        )

    try:
        # Get internal response
        internal_response = legal_ai_service.query(request.query)

        # Convert to lightweight API response
        api_response = convert_to_api_response(internal_response)

        audit_logger.log_search(request.query, len(api_response.results))

        return api_response

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def query_stream(request: QueryRequest):
    """Process search query with streaming response (not yet implemented)"""
    if not eula_service.is_eula_accepted():
        raise HTTPException(status_code=403, detail="EULA must be accepted first")

    # TODO: Implement streaming for new architecture
    raise HTTPException(
        status_code=501,
        detail="Streaming not yet implemented in new architecture. Use /query endpoint."
    )
