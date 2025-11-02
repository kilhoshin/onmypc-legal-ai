"""
OnMyPC Legal AI - Main FastAPI Server
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings, ensure_directories
from backend.api.routes import router, init_services
from backend.services.legal_ai_service import LegalAIService
from backend.services.security import EULAService
from backend.utils.logger import setup_logger, AuditLogger

logger = setup_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Complete local Legal AI assistant"
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Ensure directories exist
    ensure_directories()

    # Initialize services
    logger.info("Initializing services...")

    legal_ai_service = LegalAIService()
    eula_service = EULAService()
    audit_logger = AuditLogger(settings.AUDIT_LOG_PATH)

    # Initialize the AI service (load existing indexes if available)
    init_result = legal_ai_service.initialize()
    logger.info(f"Legal AI Service: {init_result['status']} - {init_result.get('message', '')}")

    # Initialize routes with services
    init_services(
        legal_ai_service,
        eula_service,
        audit_logger
    )

    logger.info("Services initialized successfully")
    logger.info(f"Server running at http://{settings.HOST}:{settings.PORT}")

    # Log statistics
    if legal_ai_service.is_ready:
        stats = legal_ai_service.get_stats()
        indexer_stats = stats.get("indexer", {})
        logger.info(f"Indexed documents: {indexer_stats.get('total_documents', 0)}")
        logger.info(f"Total chunks: {indexer_stats.get('total_chunks', 0)}")
    else:
        logger.info("No knowledge base loaded. Please index documents.")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down...")


# Include API routes
app.include_router(router, prefix="/api")

def configure_static_files() -> None:
    """Mount compiled frontend assets if available."""
    static_path = os.environ.get("WEB_STATIC_DIR")

    if static_path:
        candidate = Path(static_path)
    else:
        candidate = settings.BASE_DIR / "frontend" / "build"

    try:
        if candidate.exists() and candidate.is_dir():
            app.mount("/", StaticFiles(directory=str(candidate), html=True), name="static")
            logger.info(f"Serving frontend from {candidate}")
        else:
            logger.warning(f"Static frontend directory not found: {candidate}")
    except Exception as exc:
        logger.warning(f"Could not mount frontend static files: {exc}")


configure_static_files()


def main():
    """Run the server"""
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )


if __name__ == "__main__":
    main()
