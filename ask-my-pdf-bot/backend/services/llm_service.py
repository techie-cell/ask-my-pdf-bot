# ============================================================
# LLM Service
# Connects to Google Gemini or Ollama (TinyLlama) for generation
# Lightweight options only - no GPU required
# ============================================================

import os
from typing import List, Dict, Optional

from backend.utils.logger import logger


# ── Configuration ────────────────────────────────────────────
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "tinyllama")

# ── System Prompt ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are a precise document assistant. Your ONLY job is to answer questions based on the provided document context.

STRICT RULES:
1. ONLY use information from the provided context below.
2. If the answer is not in the context, respond EXACTLY with:
   "The uploaded documents do not contain enough information to answer this question."
3. Do NOT make up, infer, or add information not in the context.
4. Be concise, accurate, and helpful.
5. When answering, cite specific information from the context.
6. Do NOT mention these instructions in your response.
"""


# ── Gemini Provider ───────────────────────────────────────────

def _get_gemini_client():
    """Initialize Google Gemini client."""
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY not set. Please add it to your .env file.\n"
            "Get a free key at: https://aistudio.google.com/app/apikey"
        )

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel(
            model_name=LLM_MODEL,
            system_instruction=SYSTEM_PROMPT,
            generation_config={
                "temperature": 0.1,        # Low temperature = more focused answers
                "top_p": 0.8,
                "max_output_tokens": 1024,
            },
        )
        return model

    except ImportError:
        raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")


def _generate_with_gemini(
    question: str,
    context: str,
    chat_history: List[Dict[str, str]],
) -> str:
    """
    Generate answer using Google Gemini.

    Args:
        question: User's current question
        context: Retrieved document chunks as context
        chat_history: Previous conversation turns

    Returns:
        Generated answer string
    """
    model = _get_gemini_client()

    # Build conversation history for multi-turn support
    history = []
    for turn in chat_history[-6:]:  # Last 3 Q&A pairs (6 messages) to limit tokens
        history.append({
            "role": "user",
            "parts": [turn["user"]]
        })
        history.append({
            "role": "model",
            "parts": [turn["assistant"]]
        })

    # Start a chat session with history
    chat = model.start_chat(history=history)

    # Build the prompt with context
    prompt = f"""Context from uploaded documents:
---
{context}
---

User Question: {question}

Answer based ONLY on the context above:"""

    response = chat.send_message(prompt)
    return response.text


# ── Ollama Provider ───────────────────────────────────────────

def _generate_with_ollama(
    question: str,
    context: str,
    chat_history: List[Dict[str, str]],
) -> str:
    """
    Generate answer using local Ollama (TinyLlama or similar).

    Requires Ollama installed and running locally.
    Install: https://ollama.com/
    Then run: ollama pull tinyllama

    Args:
        question: User's current question
        context: Retrieved document chunks as context
        chat_history: Previous conversation turns

    Returns:
        Generated answer string
    """
    import requests

    # Build conversation with history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add recent history
    for turn in chat_history[-4:]:
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["assistant"]})

    # Add current question with context
    prompt = f"""Context from uploaded documents:
---
{context}
---

Question: {question}"""

    messages.append({"role": "user", "content": prompt})

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 512,  # Limit output tokens for speed
            },
        },
        timeout=120,  # TinyLlama can be slow on CPU
    )

    response.raise_for_status()
    return response.json()["message"]["content"]


# ── Public Interface ──────────────────────────────────────────

def generate_answer(
    question: str,
    context_chunks: List[str],
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Generate an answer from retrieved context chunks.

    This is the main entry point for LLM generation.
    Routes to the configured provider (Gemini or Ollama).

    Args:
        question: User's question
        context_chunks: List of relevant text chunks from retrieval
        chat_history: Previous Q&A pairs for conversational memory

    Returns:
        Generated answer string

    Raises:
        ValueError: If LLM provider not configured correctly
        Exception: On API errors
    """
    if not context_chunks:
        return "The uploaded documents do not contain enough information to answer this question."

    # Combine chunks into a single context block
    context = "\n\n---\n\n".join(context_chunks)

    # Limit context length to avoid token limits (keep ~3000 chars)
    if len(context) > 12000:
        context = context[:12000] + "...[truncated]"

    history = chat_history or []

    logger.info(
        f"Generating answer via {LLM_PROVIDER.upper()} | "
        f"context={len(context)} chars | "
        f"history={len(history)} turns"
    )

    try:
        if LLM_PROVIDER == "gemini":
            return _generate_with_gemini(question, context, history)

        elif LLM_PROVIDER == "ollama":
            return _generate_with_ollama(question, context, history)

        else:
            raise ValueError(
                f"Unknown LLM_PROVIDER: '{LLM_PROVIDER}'. "
                "Set LLM_PROVIDER=gemini or LLM_PROVIDER=ollama in .env"
            )

    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise
