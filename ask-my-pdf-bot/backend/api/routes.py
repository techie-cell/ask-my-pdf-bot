# ============================================================
# API Routes
# FastAPI endpoints for the PDF chatbot
# ============================================================

import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.services.pdf_service import extract_text_from_pdf, extract_pdf_metadata
from backend.rag.chunker import chunk_pages
from backend.vectorstore.faiss_store import get_vector_store
from backend.rag.retriever import retrieve_and_generate
from backend.utils.file_utils import (
    sanitize_filename,
    validate_pdf_file,
    get_upload_path,
    list_uploaded_files,
    delete_upload_file,
)
from backend.utils.logger import logger


# ── Router Setup ─────────────────────────────────────────────
router = APIRouter()


# ── Request/Response Models ───────────────────────────────────

class ChatMessage(BaseModel):
    """A single conversation turn."""
    user: str
    assistant: str


class QuestionRequest(BaseModel):
    """Request body for the /ask endpoint."""
    question: str
    chat_history: Optional[List[ChatMessage]] = []


class QuestionResponse(BaseModel):
    """Response from the /ask endpoint."""
    answer: str
    sources: List[dict]
    num_chunks: int


class DocumentInfo(BaseModel):
    """Information about an uploaded document."""
    filename: str
    page_count: int
    file_size_kb: float


# ── Endpoints ────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns server status and current index statistics.
    """
    store = get_vector_store()
    stats = store.get_stats()
    return {
        "status": "ok",
        "indexed_documents": stats["indexed_sources"],
        "total_chunks": stats["total_chunks"],
    }


@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and index it for RAG.

    Process:
    1. Validate file (type + size)
    2. Save to uploads/ directory
    3. Extract text page by page
    4. Split into chunks
    5. Generate embeddings
    6. Store in FAISS index

    Returns info about the indexed document.
    """
    # Read file content first to check size
    content = await file.read()
    file_size = len(content)

    # Validate the file
    is_valid, error_msg = validate_pdf_file(file.filename or "upload.pdf", file_size)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Sanitize filename
    safe_name = sanitize_filename(file.filename or "upload.pdf")
    upload_path = get_upload_path(safe_name)

    logger.info(f"Uploading file: {safe_name} ({file_size / 1024:.1f} KB)")

    # Save file to disk
    with open(upload_path, "wb") as f:
        f.write(content)

    try:
        # Extract text from PDF
        pages = extract_text_from_pdf(upload_path)

        if not pages:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Could not extract text from this PDF. "
                    "It may be scanned/image-only. Please use a text-based PDF."
                ),
            )

        # Split into chunks
        chunks = chunk_pages(pages)

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="PDF appears to have no readable text content.",
            )

        # Get metadata before embedding
        metadata = extract_pdf_metadata(upload_path)

        # Add to vector store (generates embeddings + indexes)
        store = get_vector_store()
        store.add_chunks(chunks)

        logger.info(f"Successfully indexed: {safe_name} ({len(chunks)} chunks)")

        return {
            "message": f"Successfully indexed '{safe_name}'",
            "filename": safe_name,
            "pages_extracted": len(pages),
            "chunks_created": len(chunks),
            "page_count": metadata["page_count"],
            "file_size_kb": metadata["file_size_kb"],
        }

    except HTTPException:
        raise
    except Exception as e:
        # Clean up failed upload
        if upload_path.exists():
            upload_path.unlink()
        logger.error(f"Failed to process {safe_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {str(e)}",
        )


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question against indexed PDF documents.

    Uses RAG pipeline:
    1. Embed the question
    2. Retrieve relevant chunks from FAISS
    3. Send context + question to LLM
    4. Return answer with source citations
    """
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    logger.info(f"Question received: '{request.question[:100]}'")

    # Convert ChatMessage objects to dicts for the pipeline
    history = [
        {"user": msg.user, "assistant": msg.assistant}
        for msg in (request.chat_history or [])
    ]

    # Run RAG pipeline
    response = retrieve_and_generate(
        question=request.question,
        chat_history=history,
    )

    return QuestionResponse(
        answer=response.answer,
        sources=[s.to_dict() for s in response.sources],
        num_chunks=len(response.retrieved_chunks),
    )


@router.get("/documents")
async def list_documents():
    """
    List all uploaded and indexed documents.

    Returns:
        List of indexed source names from the vector store
    """
    store = get_vector_store()
    stats = store.get_stats()

    return {
        "indexed_documents": stats["indexed_sources"],
        "total_chunks": stats["total_chunks"],
    }


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Remove a document from uploads (does not re-index remaining docs).

    Note: For simplicity, this deletes the file but requires
    re-uploading all documents to refresh the index.
    """
    deleted = delete_upload_file(filename)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filename}' not found",
        )
    return {"message": f"File '{filename}' deleted"}


@router.post("/clear")
async def clear_index():
    """
    Clear all documents from the vector store.
    Useful for starting fresh with new documents.
    """
    store = get_vector_store()
    store.clear()
    logger.info("Vector store cleared by user request")
    return {"message": "All documents cleared from index"}
