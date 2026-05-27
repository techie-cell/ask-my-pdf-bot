# ============================================================
# PDF Service
# Extracts text from PDF files using PyMuPDF (fitz)
# Lightweight, fast, no external dependencies
# ============================================================

from pathlib import Path
from typing import List, Dict, Any

import fitz  # PyMuPDF

from backend.utils.logger import logger


# ── Data Types ───────────────────────────────────────────────

class PageContent:
    """Represents extracted content from a single PDF page."""

    def __init__(self, text: str, page_number: int, source: str):
        self.text = text
        self.page_number = page_number  # 1-indexed for user display
        self.source = source            # PDF filename


def extract_text_from_pdf(file_path: Path) -> List[PageContent]:
    """
    Extract text from all pages of a PDF file.

    Uses PyMuPDF for fast, lightweight text extraction.
    Handles scanned PDFs (returns empty text for image-only pages).

    Args:
        file_path: Path to the PDF file

    Returns:
        List of PageContent objects, one per page

    Raises:
        ValueError: If file cannot be opened as PDF
        FileNotFoundError: If file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    pages: List[PageContent] = []
    source_name = file_path.name

    logger.info(f"Extracting text from: {source_name}")

    try:
        # Open the PDF document
        doc = fitz.open(str(file_path))

        total_pages = len(doc)
        logger.info(f"  → {total_pages} pages found in {source_name}")

        for page_index in range(total_pages):
            page = doc[page_index]

            # Extract text with layout preservation
            text = page.get_text("text")

            # Clean up whitespace while preserving paragraph breaks
            text = _clean_text(text)

            # Skip nearly empty pages (likely images or blank pages)
            if len(text.strip()) < 20:
                logger.debug(f"  → Skipping page {page_index + 1} (too little text)")
                continue

            pages.append(PageContent(
                text=text,
                page_number=page_index + 1,  # Convert to 1-indexed
                source=source_name,
            ))

        doc.close()
        logger.info(f"  → Extracted text from {len(pages)} pages (of {total_pages})")

    except fitz.FileDataError as e:
        raise ValueError(f"Cannot read PDF file '{source_name}': {e}")

    return pages


def extract_pdf_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract basic metadata from a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dictionary with title, author, page count, etc.
    """
    try:
        doc = fitz.open(str(file_path))
        metadata = doc.metadata or {}
        page_count = len(doc)
        doc.close()

        return {
            "filename": file_path.name,
            "page_count": page_count,
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "file_size_kb": round(file_path.stat().st_size / 1024, 1),
        }

    except Exception as e:
        logger.warning(f"Could not read metadata from {file_path.name}: {e}")
        return {
            "filename": file_path.name,
            "page_count": 0,
            "title": "",
            "author": "",
            "file_size_kb": 0,
        }


def _clean_text(text: str) -> str:
    """
    Clean extracted text by normalizing whitespace.

    Args:
        text: Raw extracted text

    Returns:
        Cleaned text
    """
    import re

    # Replace multiple spaces with single space
    text = re.sub(r" +", " ", text)

    # Replace more than 2 newlines with 2 newlines (preserve paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
