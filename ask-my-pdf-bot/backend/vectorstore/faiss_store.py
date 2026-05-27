# ============================================================
# FAISS Vector Store
# Manages the local FAISS index for storing and searching embeddings
# Saves/loads index from disk for persistence between sessions
# ============================================================

import os
import json
import pickle
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import faiss

from backend.rag.chunker import TextChunk
from backend.embeddings.embedder import embed_texts, embed_query, get_embedding_dimension
from backend.utils.logger import logger


# ── Configuration ────────────────────────────────────────────
DATA_DIR: Path = Path(os.getenv("DATA_DIR", "data"))
FAISS_INDEX_PATH: Path = DATA_DIR / "faiss_index.bin"
CHUNKS_METADATA_PATH: Path = DATA_DIR / "chunks_metadata.pkl"
TOP_K: int = int(os.getenv("TOP_K_RESULTS", "5"))


# ── FAISS Store Class ─────────────────────────────────────────

class FAISSVectorStore:
    """
    Local FAISS-based vector store for PDF chunk embeddings.

    Features:
    - Stores embeddings in memory with disk persistence
    - Fast cosine similarity search (via L2 on normalized vectors)
    - Metadata storage for source citations
    - Supports adding new documents incrementally

    Usage:
        store = FAISSVectorStore()
        store.add_chunks(chunks)
        results = store.search("What is the contract date?", top_k=5)
    """

    def __init__(self):
        self.index: Optional[faiss.Index] = None
        self.chunks: List[TextChunk] = []     # Parallel list to index rows
        self._is_loaded: bool = False

        # Try to load existing index from disk
        self._load_from_disk()

    def add_chunks(self, chunks: List[TextChunk]) -> None:
        """
        Embed and add text chunks to the FAISS index.

        Args:
            chunks: List of TextChunk objects to add
        """
        if not chunks:
            logger.warning("No chunks to add to vector store")
            return

        logger.info(f"Adding {len(chunks)} chunks to FAISS index...")

        # Extract text for embedding
        texts = [chunk.text for chunk in chunks]

        # Generate embeddings
        embeddings = embed_texts(texts)

        # Initialize FAISS index if first time
        if self.index is None:
            dim = get_embedding_dimension()
            # IndexFlatIP = Inner Product (cosine similarity for normalized vectors)
            self.index = faiss.IndexFlatIP(dim)
            logger.info(f"  → Created new FAISS index (dim={dim})")

        # Convert to float32 (FAISS requirement)
        embeddings_f32 = embeddings.astype(np.float32)

        # Add to index
        self.index.add(embeddings_f32)

        # Store chunk metadata (parallel to index)
        self.chunks.extend(chunks)

        logger.info(f"  → Index now contains {self.index.ntotal} vectors")

        # Save to disk
        self._save_to_disk()

    def search(
        self,
        query: str,
        top_k: int = TOP_K,
        score_threshold: float = 0.3,
    ) -> List[Tuple[TextChunk, float]]:
        """
        Search for the most relevant chunks for a query.

        Args:
            query: User's question
            top_k: Number of results to return
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of (TextChunk, similarity_score) tuples, sorted by relevance
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("FAISS index is empty - no documents loaded")
            return []

        # Embed the query
        query_embedding = embed_query(query)
        query_f32 = query_embedding.astype(np.float32).reshape(1, -1)

        # Search FAISS index
        actual_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_f32, actual_k)

        # Build results
        results: List[Tuple[TextChunk, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue

            # Filter by minimum score
            if float(score) < score_threshold:
                logger.debug(f"  → Skipping chunk {idx} (score={score:.3f} below threshold)")
                continue

            results.append((self.chunks[idx], float(score)))

        logger.info(
            f"Search complete: '{query[:50]}...' → {len(results)} results "
            f"(top score: {results[0][1]:.3f if results else 0:.3f})"
        )

        return results

    def clear(self) -> None:
        """Clear all vectors from the store and delete saved files."""
        self.index = None
        self.chunks = []
        self._is_loaded = False

        # Remove saved files
        for path in [FAISS_INDEX_PATH, CHUNKS_METADATA_PATH]:
            if path.exists():
                path.unlink()

        logger.info("FAISS index cleared")

    def get_indexed_sources(self) -> List[str]:
        """
        Get list of unique PDF filenames in the index.

        Returns:
            Sorted list of source filenames
        """
        if not self.chunks:
            return []
        return sorted(set(chunk.source for chunk in self.chunks))

    def get_stats(self) -> dict:
        """Get statistics about the current index."""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "total_chunks": len(self.chunks),
            "indexed_sources": self.get_indexed_sources(),
            "is_empty": self.index is None or self.index.ntotal == 0,
        }

    def _save_to_disk(self) -> None:
        """Save FAISS index and chunk metadata to disk."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)

            # Save FAISS index
            faiss.write_index(self.index, str(FAISS_INDEX_PATH))

            # Save chunk metadata (can't go into FAISS index)
            with open(CHUNKS_METADATA_PATH, "wb") as f:
                pickle.dump(self.chunks, f)

            logger.debug(f"Vector store saved: {FAISS_INDEX_PATH}")

        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def _load_from_disk(self) -> None:
        """Load saved FAISS index and metadata from disk if they exist."""
        if not FAISS_INDEX_PATH.exists() or not CHUNKS_METADATA_PATH.exists():
            logger.info("No saved vector store found - starting fresh")
            return

        try:
            # Load FAISS index
            self.index = faiss.read_index(str(FAISS_INDEX_PATH))

            # Load chunk metadata
            with open(CHUNKS_METADATA_PATH, "rb") as f:
                self.chunks = pickle.load(f)

            self._is_loaded = True
            logger.info(
                f"Loaded existing vector store: "
                f"{self.index.ntotal} vectors, "
                f"{len(self.get_indexed_sources())} documents"
            )

        except Exception as e:
            logger.warning(f"Could not load saved index (will create new): {e}")
            self.index = None
            self.chunks = []


# ── Module-level singleton ────────────────────────────────────
# Single shared instance across the application
_vector_store: Optional[FAISSVectorStore] = None


def get_vector_store() -> FAISSVectorStore:
    """Get or create the singleton FAISSVectorStore instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore()
    return _vector_store
