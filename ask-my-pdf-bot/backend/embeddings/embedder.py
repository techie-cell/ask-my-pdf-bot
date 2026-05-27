# ============================================================
# Embedding Module
# Generates vector embeddings using sentence-transformers
# Uses CPU-friendly lightweight models
# ============================================================

import os
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.utils.logger import logger


# ── Configuration ────────────────────────────────────────────
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
DEVICE: str = os.getenv("DEVICE", "cpu")

# Singleton model instance (load once, reuse)
_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Load or return the cached embedding model.

    Uses a module-level singleton to avoid reloading the model
    on every request (saves ~500MB RAM on repeated calls).

    Returns:
        Loaded SentenceTransformer model
    """
    global _model

    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL} on {DEVICE}")
        logger.info("  → This may take 30-60 seconds on first run (downloading model)...")

        _model = SentenceTransformer(
            EMBEDDING_MODEL,
            device=DEVICE,
        )

        # Log model details
        embedding_dim = _model.get_sentence_embedding_dimension()
        logger.info(f"  → Model loaded! Embedding dimension: {embedding_dim}")

    return _model


def embed_texts(texts: List[str], batch_size: int = 32) -> np.ndarray:
    """
    Generate embeddings for a list of texts.

    Uses batched encoding for memory efficiency.
    On 8GB RAM, batch_size=32 is a good balance of speed vs memory.

    Args:
        texts: List of text strings to embed
        batch_size: Number of texts to encode at once (reduce if OOM)

    Returns:
        NumPy array of shape (len(texts), embedding_dim)

    Example:
        >>> embeddings = embed_texts(["Hello world", "How are you?"])
        >>> print(embeddings.shape)  # (2, 384) for MiniLM
    """
    if not texts:
        return np.array([])

    model = get_embedding_model()

    logger.info(f"Generating embeddings for {len(texts)} texts (batch_size={batch_size})")

    # encode() handles batching internally
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 50,  # Show progress for large batches
        convert_to_numpy=True,
        normalize_embeddings=True,  # L2 normalize for cosine similarity
    )

    logger.info(f"  → Embeddings shape: {embeddings.shape}")
    return embeddings


def embed_query(query: str) -> np.ndarray:
    """
    Generate embedding for a single query string.

    Slightly different from embed_texts - adds query prefix for
    BGE models (which use "Represent this sentence for searching relevance:")
    MiniLM doesn't need the prefix, but it works fine either way.

    Args:
        query: User's question

    Returns:
        1D NumPy array of embedding values
    """
    model = get_embedding_model()

    # For BGE models, prepend the query instruction
    if "bge" in EMBEDDING_MODEL.lower():
        query = f"Represent this sentence for searching relevance: {query}"

    embedding = model.encode(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return embedding


def get_embedding_dimension() -> int:
    """
    Get the embedding dimension of the current model.

    Returns:
        Integer dimension (384 for MiniLM, 512 for BGE-small)
    """
    model = get_embedding_model()
    return model.get_sentence_embedding_dimension()
