# 📄 Ask My PDF Bot

> A lightweight, production-ready RAG-based PDF chatbot 
Upload PDF files → Ask questions → Get accurate, cited answers powered by AI.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📤 Multi-PDF Upload | Upload multiple PDFs simultaneously |
| 🔍 Smart Retrieval | FAISS vector search for relevant passages |
| 🤖 AI Answers | Powered by Google Gemini (free tier) |
| 📌 Source Citations | Every answer cites the source PDF + page number |
| 💬 Conversation Memory | Follow-up questions understand context |
| 🛡️ Hallucination Guard | Refuses to answer if info not in documents |
| 💾 Persistent Index | FAISS index saved to disk between sessions |

---

## 🏗️ Tech Stack

```
Frontend    → Streamlit
Backend     → FastAPI + Uvicorn
Embeddings  → sentence-transformers (all-MiniLM-L6-v2)
Vector DB   → FAISS (local, CPU)
PDF Parsing → PyMuPDF (fitz)
LLM         → Google Gemini 1.5 Flash (or Ollama TinyLlama)
```

---

## 📁 Project Structure

```
ask-my-pdf-bot/
│
├── backend/
│   ├── api/
│   │   └── routes.py          ← FastAPI endpoints
│   ├── rag/
│   │   ├── chunker.py         ← Text splitting logic
│   │   └── retriever.py       ← RAG pipeline orchestration
│   ├── embeddings/
│   │   └── embedder.py        ← sentence-transformers embedding
│   ├── vectorstore/
│   │   └── faiss_store.py     ← FAISS index management
│   ├── services/
│   │   ├── pdf_service.py     ← PDF text extraction
│   │   └── llm_service.py     ← Gemini/Ollama integration
│   ├── utils/
│   │   ├── logger.py          ← Loguru logging setup
│   │   └── file_utils.py      ← File validation & security
│   └── main.py                ← FastAPI app entry point
│
├── frontend/
│   └── app.py                 ← Streamlit chat UI
│
├── data/
│   ├── create_sample_pdfs.py  ← Generate test PDFs
│   ├── sample_contract.pdf    ← Auto-generated sample
│   ├── sample_policy.pdf      ← Auto-generated sample
│   └── sample_qa.json         ← Test questions
│
├── uploads/                   ← Uploaded PDFs stored here
├── logs/                      ← Application logs
├── tests/
│   └── test_basic.py          ← Unit tests
│
├── requirements.txt
├── .env.example               ← Environment variables template
├── .env                       ← Your config (create from .env.example)
├── run.bat                    ← Quick start (both servers)
└── start_project.bat          ← First-time setup + launch
```

---


## 🎮 How to Use

1. **Upload PDFs** — Use the sidebar to upload one or more PDF files
2. **Wait for indexing** — Each PDF is extracted, chunked, and embedded
3. **Ask questions** — Type in the chat box and press Enter
4. **View sources** — Each answer shows which PDF and page it came from
5. **Follow-up** — The bot remembers your conversation


## ⚙️ Configuration (`.env` file)

```env
# LLM Provider
GEMINI_API_KEY=your_key_here
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash       # Fast and free-tier friendly

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Lightweight, 384 dimensions

# RAG Settings
CHUNK_SIZE=700                    # Characters per chunk
CHUNK_OVERLAP=100                 # Overlap between chunks
TOP_K_RESULTS=5                   # Retrieved chunks per query

# Performance
DEVICE=cpu                        # Force CPU (no GPU needed)
MAX_FILE_SIZE_MB=50               # Max upload size
```

---

## 🔌 Optional: Use Ollama (No API Key Needed)

If you prefer a fully offline setup:

1. Install Ollama: https://ollama.com/download
2. Pull TinyLlama:
   ```cmd
   ollama pull tinyllama
   ```
3. Update `.env`:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=tinyllama
   ```
4. Start Ollama: `ollama serve`
5. Restart the backend

> ⚠️ TinyLlama is slower and less accurate than Gemini, but works 100% offline.

---

## 🧪 Running Tests

```cmd
venv\Scripts\activate
pytest tests/ -v
```

---

## 📡 API Documentation

With the backend running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Server status + indexed docs |
| POST | `/api/v1/upload` | Upload and index a PDF |
| POST | `/api/v1/ask` | Ask a question |
| GET | `/api/v1/documents` | List indexed documents |
| POST | `/api/v1/clear` | Clear all indexed documents |

### Example API call (PowerShell)

```powershell
# Ask a question
$body = @{
    question = "What is the license fee?"
    chat_history = @()
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/ask" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

---

## 🐛 Troubleshooting

### ❌ "Backend Offline" in the UI
- Make sure backend is running: `python backend\main.py`
- Check terminal for error messages
- Verify port 8000 is not in use: `netstat -an | findstr 8000`

### ❌ "GEMINI_API_KEY not set"
- Open `.env` file and add your key
- Restart the backend after saving

### ❌ "Could not extract text from PDF"
- Your PDF may be scanned (image-only)
- Try a different PDF with selectable text
- In Adobe Acrobat: you can run OCR to make it text-searchable

### ❌ `pip install` fails for torch
Run this specific command first:
```cmd
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### ❌ Out of memory errors
- Reduce `CHUNK_SIZE` to 500 in `.env`
- Reduce `TOP_K_RESULTS` to 3
- Restart backend after changes

### ❌ Slow embedding on first run
- Normal! The model downloads once (~90MB for MiniLM)
- Subsequent runs use the cached model
- Model cache location: `C:\Users\YourName\.cache\huggingface`

### ❌ Port already in use
```cmd
REM Kill process on port 8000
for /f "tokens=5" %a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /PID %a /F
```

### ❌ `ModuleNotFoundError`
Make sure your venv is activated:
```cmd
venv\Scripts\activate
# You should see (venv) in the prompt
```

---



## 🔒 Security Notes

- Files are validated for `.pdf` extension and size limits
- Filenames are sanitized to prevent path traversal
- Only text is extracted — no script execution from PDFs
- API keys are stored in `.env` (never commit to git)

---

## 📜 License

MIT License — Free to use and modify.

---

## 🙌 Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)
- [sentence-transformers](https://www.sbert.net/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [Google Gemini](https://ai.google.dev/)
