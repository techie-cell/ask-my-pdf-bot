# ============================================================
# Ask My PDF Bot - Streamlit Frontend
# Modern, clean chat UI with sidebar for PDF uploads
# ============================================================

import os
import sys
import json
import time
from pathlib import Path

import requests
import streamlit as st

# ── Page Configuration ────────────────────────────────────────
st.set_page_config(
    page_title="Ask My PDF",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Backend URL ───────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
API_BASE = f"{BACKEND_URL}/api/v1"


# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
/* ─── Global ─────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ─── App background ─────────────────────────── */
.stApp {
    background-color: #0f1117;
    color: #e8eaf0;
}

/* ─── Sidebar ────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #161b27;
    border-right: 1px solid #2a2f3e;
}

/* ─── Chat messages ──────────────────────────── */
.user-bubble {
    background: linear-gradient(135deg, #1e3a5f, #1a3352);
    border: 1px solid #2d5a8e;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    margin: 8px 0;
    margin-left: 20%;
    color: #e8f4fd;
    font-size: 0.95rem;
    line-height: 1.6;
}

.assistant-bubble {
    background: linear-gradient(135deg, #1a2035, #161c2d);
    border: 1px solid #2a3248;
    border-radius: 18px 18px 18px 4px;
    padding: 14px 18px;
    margin: 8px 0;
    margin-right: 20%;
    color: #d8dce8;
    font-size: 0.95rem;
    line-height: 1.7;
}

/* ─── Source citations box ───────────────────── */
.source-box {
    background: #0d1520;
    border: 1px solid #1e3a5f;
    border-left: 3px solid #3a7bd5;
    border-radius: 8px;
    padding: 10px 14px;
    margin-top: 10px;
    font-size: 0.82rem;
    color: #8899bb;
}

.source-item {
    display: inline-block;
    background: #1e3a5f;
    color: #7eb8f7;
    border-radius: 20px;
    padding: 2px 10px;
    margin: 3px 3px;
    font-size: 0.78rem;
    font-family: 'DM Mono', monospace;
}

/* ─── Header ─────────────────────────────────── */
.app-header {
    text-align: center;
    padding: 20px 0 10px;
}

.app-header h1 {
    font-size: 2rem;
    font-weight: 600;
    background: linear-gradient(135deg, #5b9bd5, #7eb8f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.app-header p {
    color: #606880;
    font-size: 0.9rem;
    margin-top: 4px;
}

/* ─── Status badge ───────────────────────────── */
.status-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}
.status-ok   { background: #0d2e1a; color: #4caf50; border: 1px solid #2d6a3a; }
.status-err  { background: #2e0d0d; color: #f44336; border: 1px solid #6a2d2d; }

/* ─── File list ──────────────────────────────── */
.file-chip {
    display: inline-block;
    background: #1a2540;
    color: #7eb8f7;
    border: 1px solid #2d4a7a;
    border-radius: 6px;
    padding: 4px 10px;
    margin: 3px 2px;
    font-size: 0.82rem;
}

/* ─── Empty state ────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #3a4055;
}

.empty-state .icon {
    font-size: 4rem;
    display: block;
    margin-bottom: 16px;
}

/* ─── Streamlit overrides ────────────────────── */
.stTextInput > div > div > input {
    background: #161b27 !important;
    color: #e8eaf0 !important;
    border: 1px solid #2a3248 !important;
    border-radius: 10px !important;
}

.stButton > button {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
}

div[data-testid="stFileUploader"] {
    background: #161b27;
    border: 2px dashed #2a3a5e;
    border-radius: 12px;
    padding: 10px;
}

.stSpinner > div {
    border-top-color: #3a7bd5 !important;
}

/* Scrollable chat area */
.chat-container {
    max-height: 65vh;
    overflow-y: auto;
    padding-right: 8px;
}
</style>
""", unsafe_allow_html=True)


# ── Session State Initialization ──────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []          # [{user: str, assistant: str, sources: list}]

if "indexed_docs" not in st.session_state:
    st.session_state.indexed_docs = []

if "backend_ok" not in st.session_state:
    st.session_state.backend_ok = False


# ── Helper Functions ──────────────────────────────────────────

def check_backend() -> bool:
    """Ping backend health endpoint."""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.indexed_docs = data.get("indexed_documents", [])
            return True
    except Exception:
        pass
    return False


def upload_pdf(file_bytes: bytes, filename: str) -> dict:
    """Upload a PDF file to the backend."""
    resp = requests.post(
        f"{API_BASE}/upload",
        files={"file": (filename, file_bytes, "application/pdf")},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def ask_question(question: str, history: list) -> dict:
    """Send a question to the backend RAG pipeline."""
    payload = {
        "question": question,
        "chat_history": [
            {"user": h["user"], "assistant": h["assistant"]}
            for h in history[-6:]   # send last 6 turns only
        ],
    }
    resp = requests.post(
        f"{API_BASE}/ask",
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def clear_index() -> None:
    """Clear all indexed documents."""
    requests.post(f"{API_BASE}/clear", timeout=10)
    st.session_state.indexed_docs = []


def format_sources(sources: list) -> str:
    """Format source citations as HTML."""
    if not sources:
        return ""
    chips = "".join(
        f'<span class="source-item">📄 {s["source"]} · p.{s["page_number"]}</span>'
        for s in sources
    )
    return f'<div class="source-box">📌 <strong>Sources:</strong><br>{chips}</div>'


# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📄 Ask My PDF")
    st.markdown("---")

    # Backend status
    backend_ok = check_backend()
    st.session_state.backend_ok = backend_ok

    if backend_ok:
        st.markdown('<span class="status-badge status-ok">● Backend Online</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-err">● Backend Offline</span>', unsafe_allow_html=True)
        st.warning("Start the backend first:\n```\npython backend/main.py\n```")

    st.markdown("---")

    # ── PDF Upload Section ─────────────────────────────────
    st.markdown("### 📤 Upload PDFs")
    uploaded_files = st.file_uploader(
        "Drop PDF files here",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more PDF files (max 50MB each)",
        label_visibility="collapsed",
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_bytes = uploaded_file.read()
            fname = uploaded_file.name

            # Skip already-indexed files
            if fname in st.session_state.indexed_docs:
                st.info(f"✓ Already indexed: {fname}")
                continue

            with st.spinner(f"Processing {fname}..."):
                try:
                    result = upload_pdf(file_bytes, fname)
                    st.success(
                        f"✅ **{fname}**\n\n"
                        f"• {result.get('pages_extracted', 0)} pages extracted\n"
                        f"• {result.get('chunks_created', 0)} chunks indexed"
                    )
                    # Refresh indexed docs
                    check_backend()
                except requests.HTTPError as e:
                    try:
                        detail = e.response.json().get("detail", str(e))
                    except Exception:
                        detail = str(e)
                    st.error(f"❌ Failed: {detail}")
                except Exception as e:
                    st.error(f"❌ Connection error: {e}")

    st.markdown("---")

    # ── Indexed Documents ──────────────────────────────────
    st.markdown("### 📚 Indexed Documents")
    if st.session_state.indexed_docs:
        for doc in st.session_state.indexed_docs:
            st.markdown(f'<div class="file-chip">📄 {doc}</div>', unsafe_allow_html=True)
    else:
        st.caption("No documents indexed yet.")

    st.markdown("---")

    # ── Controls ───────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Docs", use_container_width=True, help="Remove all indexed documents"):
            if backend_ok:
                clear_index()
                st.success("Cleared!")
                time.sleep(0.5)
                st.rerun()

    with col2:
        if st.button("💬 New Chat", use_container_width=True, help="Start a fresh conversation"):
            st.session_state.chat_history = []
            st.rerun()

    # ── Download Chat History ──────────────────────────────
    if st.session_state.chat_history:
        chat_export = json.dumps(st.session_state.chat_history, indent=2)
        st.download_button(
            label="⬇️ Download Chat",
            data=chat_export,
            file_name="chat_history.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown(
        '<div style="color:#3a4055; font-size:0.75rem; text-align:center;">'
        'Ask My PDF Bot v1.0<br>CPU Optimized • RAG Powered'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Main Chat Area ────────────────────────────────────────────

# App header
st.markdown("""
<div class="app-header">
    <h1>📄 Ask My PDF Bot</h1>
    <p>Upload PDFs → Ask questions → Get cited answers</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Chat History Display ──────────────────────────────────────
chat_container = st.container()

with chat_container:
    if not st.session_state.chat_history:
        st.markdown("""
        <div class="empty-state">
            <span class="icon">💬</span>
            <h3 style="color:#4a5568; font-weight:500;">No conversation yet</h3>
            <p style="color:#3a4055;">Upload a PDF in the sidebar, then ask a question below.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for turn in st.session_state.chat_history:
            # User bubble
            st.markdown(
                f'<div class="user-bubble">🧑 {turn["user"]}</div>',
                unsafe_allow_html=True,
            )
            # Assistant bubble
            st.markdown(
                f'<div class="assistant-bubble">🤖 {turn["assistant"]}</div>',
                unsafe_allow_html=True,
            )
            # Sources
            if turn.get("sources"):
                st.markdown(format_sources(turn["sources"]), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

st.markdown("---")

# ── Question Input ────────────────────────────────────────────
col_input, col_send = st.columns([9, 1])

with col_input:
    question = st.text_input(
        "Ask a question",
        placeholder="e.g. What is the main topic of the document? Who are the parties in the contract?",
        label_visibility="collapsed",
        key="question_input",
        disabled=not st.session_state.backend_ok,
    )

with col_send:
    send_clicked = st.button(
        "➤",
        use_container_width=True,
        disabled=not st.session_state.backend_ok,
        help="Send question",
    )

# ── Handle Question Submission ────────────────────────────────
if (send_clicked or question) and question.strip():
    if not st.session_state.indexed_docs:
        st.warning("⚠️ Please upload at least one PDF document first.")
    elif not st.session_state.backend_ok:
        st.error("❌ Backend is offline. Please start the backend server.")
    else:
        with st.spinner("🔍 Searching documents and generating answer..."):
            try:
                result = ask_question(question.strip(), st.session_state.chat_history)

                # Save to chat history
                st.session_state.chat_history.append({
                    "user": question.strip(),
                    "assistant": result["answer"],
                    "sources": result.get("sources", []),
                    "num_chunks": result.get("num_chunks", 0),
                })

                # Clear input and rerun to show new message
                st.rerun()

            except requests.HTTPError as e:
                try:
                    detail = e.response.json().get("detail", str(e))
                except Exception:
                    detail = str(e)
                st.error(f"❌ Error: {detail}")
            except Exception as e:
                st.error(f"❌ Connection error: {e}\n\nMake sure the backend is running.")

# ── Footer hint ───────────────────────────────────────────────
if not st.session_state.backend_ok:
    st.info(
        "🚀 **Backend not running.** Open a terminal and run:\n\n"
        "```\npython backend/main.py\n```"
    )
