"""
Logging and audit trail utilities
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup application logger"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


class AuditLogger:
    """Audit trail logger for tracking user actions"""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        user_id: str = "local_user"
    ):
        """Log an audit event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "data": data
        }

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def log_search(self, query: str, results_count: int):
        """Log a search query"""
        self.log_event("search", {
            "query": query,
            "results_count": results_count
        })

    def log_document_access(self, document_id: str, document_name: str):
        """Log document access"""
        self.log_event("document_access", {
            "document_id": document_id,
            "document_name": document_name
        })

    def log_indexing(self, documents_count: int, duration_seconds: float):
        """Log indexing operation"""
        self.log_event("indexing", {
            "documents_count": documents_count,
            "duration_seconds": duration_seconds
        })
