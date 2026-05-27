# ============================================================
# Text Chunker
# Splits extracted PDF text into overlapping chunks
# Uses RecursiveCharacterTextSplitter for smart splitting
# ============================================================

import os
from typing import List, Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.services.pdf_service import PageContent
from backend.utils.logger import logger


# ── Configuration ────────────────────────────────────────────
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "700"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))


# ── Data Types ───────────────────────────────────────────────

class TextChunk:
    """
    Represents a single chunk of text with its source metadata.
    Used for embedding and retrieval.
    """

    def __init__(
        self,
        text: str,
        source: str,
        page_number: int,
        chunk_index: int,
    ):
        self.text = text
        self.source = source          # PDF filename
        self.page_number = page_number
        self.chunk_index = chunk_index  # Position within document

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for storage/serialization."""
        return {
            "text": self.text,
            "source": self.source,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
        }

    def __repr__(self) -> str:
        preview = self.text[:60].replace("\n", " ")
        return f"TextChunk(source={self.source}, page={self.page_number}, preview='{preview}...')"


def chunk_pages(pages: List[PageContent]) -> List[TextChunk]:
    """
    Split extracted PDF pages into overlapping text chunks.

    Strategy:
    - Each page is split independently to preserve page metadata
    - RecursiveCharacterTextSplitter tries to split on paragraphs,
      then sentences, then words (smart natural splitting)
    - Overlap ensures context isn't lost at chunk boundaries

    Args:
        pages: List of PageContent objects from PDF extraction

    Returns:
        List of TextChunk objects ready for embedding

    Example:
        >>> pages = extract_text_from_pdf(path)
        >>> chunks = chunk_pages(pages)
        >>> print(f"Created {len(chunks)} chunks from {len(pages)} pages")
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        # Try to split on natural boundaries first
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks: List[TextChunk] = []
    global_chunk_index = 0

    for page in pages:
        # Skip very short pages
        if len(page.text.strip()) < 30:
            continue

        # Split this page's text into chunks
        raw_chunks = splitter.split_text(page.text)

        for raw_chunk in raw_chunks:
            # Skip empty chunks
            if not raw_chunk.strip():
                continue

            all_chunks.append(TextChunk(
                text=raw_chunk.strip(),
                source=page.source,
                page_number=page.page_number,
                chunk_index=global_chunk_index,
            ))
            global_chunk_index += 1

    logger.info(
        f"Chunking complete: {len(pages)} pages → {len(all_chunks)} chunks "
        f"(chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})"
    )

    return all_chunks


def chunk_documents(pages_per_doc: Dict[str, List[PageContent]]) -> List[TextChunk]:
    """
    Chunk multiple documents at once.

    Args:
        pages_per_doc: Dictionary mapping filename to list of PageContent

    Returns:
        Combined list of TextChunks from all documents
    """
    all_chunks: List[TextChunk] = []

    for filename, pages in pages_per_doc.items():
        logger.info(f"Chunking: {filename} ({len(pages)} pages)")
        chunks = chunk_pages(pages)
        all_chunks.extend(chunks)

    return all_chunks
