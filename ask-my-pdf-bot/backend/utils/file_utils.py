# ============================================================
# File Utilities
# Handles file validation, sanitization, and management
# ============================================================

import os
import re
import hashlib
from pathlib import Path
from typing import Tuple

from backend.utils.logger import logger


# ── Constants ────────────────────────────────────────────────
MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
ALLOWED_EXTENSIONS: set = {".pdf"}
UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "uploads"))


def sanitize_filename(filename: str) -> str:
    """
    Remove dangerous characters from filenames.
    Prevents path traversal and shell injection attacks.

    Args:
        filename: Original filename from upload

    Returns:
        Safe, sanitized filename
    """
    # Get only the base filename (no directory components)
    filename = Path(filename).name

    # Replace spaces with underscores
    filename = filename.replace(" ", "_")

    # Remove characters that are not alphanumeric, dots, hyphens, underscores
    filename = re.sub(r"[^\w\-.]", "", filename)

    # Remove leading dots (hidden files)
    filename = filename.lstrip(".")

    # Truncate to reasonable length
    if len(filename) > 200:
        stem = Path(filename).stem[:195]
        suffix = Path(filename).suffix
        filename = f"{stem}{suffix}"

    return filename or "unnamed.pdf"


def validate_pdf_file(filename: str, file_size_bytes: int) -> Tuple[bool, str]:
    """
    Validate that the uploaded file is a safe PDF.

    Args:
        filename: Name of the uploaded file
        file_size_bytes: Size of file in bytes

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    # Check file extension
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return False, f"Only PDF files are allowed. Got: {suffix}"

    # Check file size
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size_bytes > max_bytes:
        size_mb = file_size_bytes / (1024 * 1024)
        return False, f"File too large: {size_mb:.1f} MB. Maximum allowed: {MAX_FILE_SIZE_MB} MB"

    if file_size_bytes == 0:
        return False, "File is empty"

    return True, ""


def get_file_hash(file_path: Path) -> str:
    """
    Compute MD5 hash of a file for deduplication.

    Args:
        file_path: Path to the file

    Returns:
        MD5 hash string
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def ensure_directories() -> None:
    """
    Create required application directories if they don't exist.
    Safe to call multiple times.
    """
    dirs = [
        Path(os.getenv("UPLOAD_DIR", "uploads")),
        Path(os.getenv("DATA_DIR", "data")),
        Path(os.getenv("LOGS_DIR", "logs")),
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory ensured: {directory}")


def get_upload_path(filename: str) -> Path:
    """
    Get the full path for an uploaded file.

    Args:
        filename: Sanitized filename

    Returns:
        Full path in uploads directory
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR / filename


def list_uploaded_files() -> list[str]:
    """
    List all PDF files currently in the uploads directory.

    Returns:
        List of filenames
    """
    if not UPLOAD_DIR.exists():
        return []
    return [f.name for f in UPLOAD_DIR.iterdir() if f.suffix.lower() == ".pdf"]


def delete_upload_file(filename: str) -> bool:
    """
    Delete a specific uploaded file.

    Args:
        filename: Name of file to delete

    Returns:
        True if deleted, False if not found
    """
    file_path = UPLOAD_DIR / sanitize_filename(filename)
    if file_path.exists():
        file_path.unlink()
        logger.info(f"Deleted file: {filename}")
        return True
    return False
