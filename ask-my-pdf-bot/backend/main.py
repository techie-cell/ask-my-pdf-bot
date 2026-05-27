# ============================================================
# Ask My PDF Bot - Backend Entry Point
# FastAPI application with CORS, logging, and startup events
# ============================================================

import os
import sys
from pathlib import Path

# Add project root to Python path so imports work correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load .env file FIRST before any other imports
load_dotenv()

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.utils.file_utils import ensure_directories
from backend.utils.logger import logger


# ── Application Setup ─────────────────────────────────────────

app = FastAPI(
    title="Ask My PDF Bot",
    description="RAG-powered PDF chatbot - CPU optimized for Windows 10",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",     # ReDoc UI at http://localhost:8000/redoc
)

# ── CORS (needed for Streamlit frontend to call backend) ──────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # Allow all origins in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routes ───────────────────────────────────────────
app.include_router(router, prefix="/api/v1", tags=["PDF Chatbot"])


# ── Startup / Shutdown Events ─────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """
    Runs when the server starts.
    Creates required directories and logs startup info.
    """
    logger.info("=" * 50)
    logger.info("Ask My PDF Bot - Starting up")
    logger.info("=" * 50)

    # Create all required directories
    ensure_directories()

    # Log configuration
    logger.info(f"LLM Provider : {os.getenv('LLM_PROVIDER', 'gemini')}")
    logger.info(f"LLM Model    : {os.getenv('LLM_MODEL', 'gemini-1.5-flash')}")
    logger.info(f"Embeddings   : {os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')}")
    logger.info(f"Device       : {os.getenv('DEVICE', 'cpu')}")
    logger.info(f"Upload Dir   : {os.getenv('UPLOAD_DIR', 'uploads')}")
    logger.info("")
    logger.info("API Docs     : http://localhost:8000/docs")
    logger.info("Health Check : http://localhost:8000/api/v1/health")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Runs when server is shutting down."""
    logger.info("Ask My PDF Bot - Shutting down")


# ── Root Endpoint ─────────────────────────────────────────────

@app.get("/")
async def root():
    """Root endpoint - confirms API is running."""
    return {
        "message": "Ask My PDF Bot API is running!",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


# ── Run Server ────────────────────────────────────────────────

if __name__ == "__main__":
    host = os.getenv("BACKEND_HOST", "127.0.0.1")
    port = int(os.getenv("BACKEND_PORT", "8000"))

    logger.info(f"Starting server on http://{host}:{port}")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=False,      # Set True for development hot-reload
        workers=1,         # Keep at 1 for low-RAM systems
        log_level="info",
    )
