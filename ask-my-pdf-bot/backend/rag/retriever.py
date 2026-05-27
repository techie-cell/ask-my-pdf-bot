# ============================================================
# RAG Retriever
# Orchestrates the Retrieval-Augmented Generation pipeline
# Handles: search → deduplicate → format → generate
# ============================================================

import os
from typing import List, Dict, Any, Optional, Tuple

from backend.vectorstore.faiss_store import get_vector_store
from backend.rag.chunker import TextChunk
from backend.services.llm_service import generate_answer
from backend.utils.logger import logger


# ── Configuration ────────────────────────────────────────────
TOP_K: int = int(os.getenv("TOP_K_RESULTS", "5"))

# If similarity score is below this, consider as "not found"
MIN_RELEVANCE_SCORE: float = 0.30


# ── Data Types ───────────────────────────────────────────────

class SourceCitation:
    """Represents a source citation for an answer."""

    def __init__(self, source: str, page_number: int, score: float):
        self.source = source          # PDF filename
        self.page_number = page_number
        self.score = score            # Similarity score (0-1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "page_number": self.page_number,
            "score": round(self.score, 3),
        }

    def __repr__(self) -> str:
        return f"SourceCitation({self.source}, page={self.page_number}, score={self.score:.3f})"


class RAGResponse:
    """Complete response from the RAG pipeline."""

    def __init__(
        self,
        answer: str,
        sources: List[SourceCitation],
        retrieved_chunks: List[str],
    ):
        self.answer = answer
        self.sources = sources
        self.retrieved_chunks = retrieved_chunks

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "sources": [s.to_dict() for s in self.sources],
            "num_chunks_used": len(self.retrieved_chunks),
        }


# ── Main RAG Pipeline ─────────────────────────────────────────

def retrieve_and_generate(
    question: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    top_k: int = TOP_K,
) -> RAGResponse:
    """
    Full RAG pipeline: retrieve relevant chunks, generate answer.

    Pipeline steps:
    1. Search vector store for relevant chunks
    2. Filter by minimum relevance score
    3. Deduplicate chunks (same content from different search passes)
    4. Format context for LLM
    5. Generate answer with source attribution
    6. Return answer + citations

    Args:
        question: User's question
        chat_history: Previous conversation turns
        top_k: Number of chunks to retrieve

    Returns:
        RAGResponse with answer and source citations
    """
    vector_store = get_vector_store()

    # ── Step 1: Check if index has content ───────────────────
    stats = vector_store.get_stats()
    if stats["is_empty"]:
        return RAGResponse(
            answer="Please upload PDF documents first before asking questions.",
            sources=[],
            retrieved_chunks=[],
        )

    # ── Step 2: Retrieve relevant chunks ─────────────────────
    logger.info(f"Retrieving chunks for: '{question[:80]}...'")

    search_results: List[Tuple[TextChunk, float]] = vector_store.search(
        query=question,
        top_k=top_k,
        score_threshold=MIN_RELEVANCE_SCORE,
    )

    # ── Step 3: Handle no relevant results ───────────────────
    if not search_results:
        logger.info("No relevant chunks found above threshold")
        return RAGResponse(
            answer="The uploaded documents do not contain enough information to answer this question.",
            sources=[],
            retrieved_chunks=[],
        )

    # ── Step 4: Deduplicate and format context ────────────────
    context_texts: List[str] = []
    sources: List[SourceCitation] = []
    seen_texts: set = set()

    for chunk, score in search_results:
        # Skip near-duplicate chunks
        text_preview = chunk.text[:100]
        if text_preview in seen_texts:
            continue
        seen_texts.add(text_preview)

        # Format chunk with source header for the LLM
        formatted = (
            f"[Source: {chunk.source}, Page {chunk.page_number}]\n"
            f"{chunk.text}"
        )
        context_texts.append(formatted)

        # Track unique source citations
        citation = SourceCitation(
            source=chunk.source,
            page_number=chunk.page_number,
            score=score,
        )
        # Avoid duplicate citations
        is_duplicate = any(
            s.source == citation.source and s.page_number == citation.page_number
            for s in sources
        )
        if not is_duplicate:
            sources.append(citation)

    logger.info(
        f"Context prepared: {len(context_texts)} chunks from "
        f"{len(set(s.source for s in sources))} documents"
    )

    # ── Step 5: Generate answer ───────────────────────────────
    try:
        answer = generate_answer(
            question=question,
            context_chunks=context_texts,
            chat_history=chat_history or [],
        )

    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        answer = f"Sorry, I encountered an error generating the answer: {str(e)}"
        sources = []

    # ── Step 6: Return response ───────────────────────────────
    return RAGResponse(
        answer=answer,
        sources=sorted(sources, key=lambda s: s.score, reverse=True),
        retrieved_chunks=context_texts,
    )
