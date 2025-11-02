"""
Folder Manager - Track indexed document folders
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FolderManager:
    """Manages the list of indexed document folders"""

    def __init__(self, storage_path: Path):
        """
        Initialize folder manager

        Args:
            storage_path: Path to store folder metadata (e.g., data/indexed_folders.json)
        """
        self.storage_path = storage_path
        self.folders = self._load_folders()

    def _load_folders(self) -> List[Dict]:
        """Load folder list from disk"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('folders', [])
            except Exception as e:
                logger.error(f"Failed to load folder list: {e}")
                return []
        return []

    def _save_folders(self):
        """Save folder list to disk"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump({'folders': self.folders}, f, indent=2, default=str)
            logger.info(f"Saved {len(self.folders)} folders to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save folder list: {e}")

    def add_folder(self, folder_path: str, document_count: int = 0):
        """
        Add or update a folder in the tracked list

        Args:
            folder_path: Absolute path to the folder
            document_count: Number of documents indexed from this folder
        """
        folder_path = str(Path(folder_path).resolve())

        # Check if folder already exists
        existing = None
        for folder in self.folders:
            if folder['path'] == folder_path:
                existing = folder
                break

        now = datetime.now().isoformat()

        if existing:
            # Update existing folder
            existing['last_indexed'] = now
            existing['document_count'] = document_count
            logger.info(f"Updated folder: {folder_path}")
        else:
            # Add new folder
            self.folders.append({
                'path': folder_path,
                'added_at': now,
                'last_indexed': now,
                'document_count': document_count
            })
            logger.info(f"Added new folder: {folder_path}")

        self._save_folders()

    def remove_folder(self, folder_path: str) -> bool:
        """
        Remove a folder from the tracked list

        Args:
            folder_path: Path to remove

        Returns:
            True if removed, False if not found
        """
        folder_path = str(Path(folder_path).resolve())

        original_count = len(self.folders)
        self.folders = [f for f in self.folders if f['path'] != folder_path]

        if len(self.folders) < original_count:
            self._save_folders()
            logger.info(f"Removed folder: {folder_path}")
            return True

        return False

    def get_folders(self) -> List[Dict]:
        """Get list of all tracked folders"""
        return self.folders

    def get_folder(self, folder_path: str) -> Optional[Dict]:
        """Get info for a specific folder"""
        folder_path = str(Path(folder_path).resolve())
        for folder in self.folders:
            if folder['path'] == folder_path:
                return folder
        return None

    def clear_all(self):
        """Clear all tracked folders"""
        self.folders = []
        self._save_folders()
        logger.info("Cleared all tracked folders")
