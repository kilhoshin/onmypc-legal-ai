"""
Security and encryption services
"""
import hashlib
import secrets
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from backend.config import settings
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class EncryptionService:
    """Handles AES-256 encryption for sensitive data"""

    def __init__(self, password: Optional[str] = None):
        self.password = password or self._get_or_create_key()
        self.cipher = self._initialize_cipher()

    def _get_or_create_key(self) -> str:
        """Get or create encryption key"""
        key_file = settings.DATA_DIR / ".key"

        if key_file.exists():
            with open(key_file, "rb") as f:
                return f.read().decode()
        else:
            # Generate new key
            key = secrets.token_urlsafe(32)
            settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(key_file, "wb") as f:
                f.write(key.encode())
            # Set file permissions (Windows)
            try:
                import os
                os.chmod(key_file, 0o600)
            except Exception as e:
                logger.warning(f"Could not set key file permissions: {e}")
            return key

    def _initialize_cipher(self) -> Fernet:
        """Initialize Fernet cipher"""
        # Derive key from password using PBKDF2HMAC
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"onmypc_legal_ai_salt",  # In production, use random salt
            iterations=100000,
        )
        key = kdf.derive(self.password.encode())
        # Fernet requires base64-encoded key
        from base64 import urlsafe_b64encode
        fernet_key = urlsafe_b64encode(key)
        return Fernet(fernet_key)

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data"""
        return self.cipher.encrypt(data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data"""
        return self.cipher.decrypt(encrypted_data)

    def encrypt_text(self, text: str) -> str:
        """Encrypt text and return base64 string"""
        encrypted = self.encrypt(text.encode())
        return encrypted.decode()

    def decrypt_text(self, encrypted_text: str) -> str:
        """Decrypt base64 string to text"""
        decrypted = self.decrypt(encrypted_text.encode())
        return decrypted.decode()


class EULAService:
    """Manages EULA acceptance and tracking"""

    def __init__(self):
        self.eula_file = settings.DATA_DIR / ".eula_accepted"
        self.eula_version = settings.EULA_VERSION

    def is_eula_accepted(self) -> bool:
        """Check if EULA has been accepted"""
        if not self.eula_file.exists():
            return False

        with open(self.eula_file, "r") as f:
            version = f.read().strip()
            return version == self.eula_version

    def accept_eula(self) -> bool:
        """Mark EULA as accepted"""
        try:
            settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.eula_file, "w") as f:
                f.write(self.eula_version)
            logger.info(f"EULA {self.eula_version} accepted")
            return True
        except Exception as e:
            logger.error(f"Failed to save EULA acceptance: {e}")
            return False

    def get_eula_text(self) -> str:
        """Get EULA text"""
        return """
OnMyPC Legal AI - End User License Agreement (EULA)

Version 1.0

IMPORTANT LEGAL DISCLAIMER:

1. NOT LEGAL ADVICE
   This software provides AI-assisted document search and summarization.
   All results are for informational purposes only and DO NOT constitute
   legal advice. You must consult with a qualified attorney for legal matters.

2. USER RESPONSIBILITY
   All responsibility for decisions made based on this software's output
   lies solely with you, the user. You must independently verify all
   information before relying on it.

3. NO WARRANTIES
   This software is provided "AS IS" without warranties of any kind,
   either express or implied.

4. LIMITATION OF LIABILITY
   The developers shall not be liable for any damages arising from the
   use or inability to use this software.

5. DATA PRIVACY
   All data processing occurs locally on your computer. No data is sent
   to external servers. You are responsible for securing your own data.

6. COMPLIANCE
   You are responsible for ensuring your use of this software complies
   with all applicable laws, including attorney-client privilege and
   confidentiality requirements.

By clicking "I Accept", you acknowledge that you have read and agree
to all terms above.
        """.strip()


def hash_file(file_path: Path) -> str:
    """Generate SHA-256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
