"""
OnMyPC Legal AI - Configuration
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "OnMyPC Legal AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DOCS_DIR: Path = Path.home() / "Documents" / "LegalDocs"
    INDEX_DIR: Path = DATA_DIR / "index"
    DB_PATH: Path = DATA_DIR / "legal_ai.db"
    AUDIT_LOG_PATH: Path = DATA_DIR / "audit.jsonl"

    # AI Models
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RERANKER_MODEL: str = "BAAI/bge-reranker-base"
    # Search Settings
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5
    RERANK_TOP_K: int = 3

    # Security
    ENCRYPTION_ENABLED: bool = True
    ENCRYPTION_KEY: Optional[str] = None

    # Legal Disclaimer
    EULA_VERSION: str = "1.0"
    DISCLAIMER_TEXT: str = (
        "Results are generated from your indexed documents. "
        "Review and verify before taking action."
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def ensure_directories():
    """Create necessary directories if they don't exist"""
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    settings.DOCS_DIR.mkdir(parents=True, exist_ok=True)
