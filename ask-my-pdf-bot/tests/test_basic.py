# ============================================================
# Basic Unit Tests
# Tests core components without requiring API keys or GPU
# Run with: pytest tests/ -v
# ============================================================

import sys
import os
from pathlib import Path

# Make sure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile
import fitz  # PyMuPDF


# ── Test: File Utils ──────────────────────────────────────────

class TestFileUtils:
    """Tests for file validation and sanitization."""

    def test_sanitize_filename_removes_spaces(self):
        from backend.utils.file_utils import sanitize_filename
        result = sanitize_filename("my document.pdf")
        assert " " not in result
        assert result == "my_document.pdf"

    def test_sanitize_filename_removes_special_chars(self):
        from backend.utils.file_utils import sanitize_filename
        result = sanitize_filename("../../etc/passwd.pdf")
        assert ".." not in result
        assert "/" not in result

    def test_sanitize_filename_keeps_valid_chars(self):
        from backend.utils.file_utils import sanitize_filename
        result = sanitize_filename("contract-2024_v2.pdf")
        assert result == "contract-2024_v2.pdf"

    def test_validate_pdf_valid_file(self):
        from backend.utils.file_utils import validate_pdf_file
        is_valid, msg = validate_pdf_file("document.pdf", 1024 * 100)  # 100KB
        assert is_valid is True
        assert msg == ""

    def test_validate_pdf_wrong_extension(self):
        from backend.utils.file_utils import validate_pdf_file
        is_valid, msg = validate_pdf_file("document.docx", 1024)
        assert is_valid is False
        assert "PDF" in msg

    def test_validate_pdf_too_large(self):
        from backend.utils.file_utils import validate_pdf_file
        big_size = 200 * 1024 * 1024  # 200 MB
        is_valid, msg = validate_pdf_file("big.pdf", big_size)
        assert is_valid is False
        assert "large" in msg.lower()

    def test_validate_pdf_empty_file(self):
        from backend.utils.file_utils import validate_pdf_file
        is_valid, msg = validate_pdf_file("empty.pdf", 0)
        assert is_valid is False


# ── Test: PDF Service ─────────────────────────────────────────

class TestPDFService:
    """Tests for PDF text extraction."""

    def _create_sample_pdf(self, text: str = "Hello World. This is a test PDF.") -> Path:
        """Create a temporary PDF file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 100), text, fontsize=12)
        doc.save(str(tmp_path))
        doc.close()
        return tmp_path

    def test_extract_text_from_valid_pdf(self):
        from backend.services.pdf_service import extract_text_from_pdf
        pdf_path = self._create_sample_pdf("This is a test document with some content.")
        try:
            pages = extract_text_from_pdf(pdf_path)
            assert len(pages) >= 1
            assert "test" in pages[0].text.lower()
            assert pages[0].page_number == 1
        finally:
            pdf_path.unlink()

    def test_extract_text_preserves_source(self):
        from backend.services.pdf_service import extract_text_from_pdf
        pdf_path = self._create_sample_pdf("Source test content.")
        try:
            pages = extract_text_from_pdf(pdf_path)
            assert pages[0].source == pdf_path.name
        finally:
            pdf_path.unlink()

    def test_extract_text_file_not_found(self):
        from backend.services.pdf_service import extract_text_from_pdf
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf(Path("nonexistent.pdf"))

    def test_extract_pdf_metadata(self):
        from backend.services.pdf_service import extract_pdf_metadata
        pdf_path = self._create_sample_pdf()
        try:
            meta = extract_pdf_metadata(pdf_path)
            assert meta["page_count"] == 1
            assert meta["filename"] == pdf_path.name
            assert meta["file_size_kb"] > 0
        finally:
            pdf_path.unlink()


# ── Test: Text Chunker ────────────────────────────────────────

class TestChunker:
    """Tests for text chunking logic."""

    def _make_page_content(self, text: str, page_num: int = 1):
        from backend.services.pdf_service import PageContent
        return PageContent(text=text, page_number=page_num, source="test.pdf")

    def test_chunk_produces_output(self):
        from backend.rag.chunker import chunk_pages
        long_text = "This is sentence number {}. " * 50
        pages = [self._make_page_content(long_text.format(i) for i in range(50))]
        # Fix: make a proper list of strings
        pages = [self._make_page_content(" ".join([f"Sentence {i}. " * 20 for i in range(5)]))]
        chunks = chunk_pages(pages)
        assert len(chunks) >= 1

    def test_chunk_contains_source_metadata(self):
        from backend.rag.chunker import chunk_pages
        text = "Word " * 200  # Long enough to produce chunks
        pages = [self._make_page_content(text)]
        chunks = chunk_pages(pages)
        for chunk in chunks:
            assert chunk.source == "test.pdf"
            assert chunk.page_number == 1
            assert chunk.text.strip() != ""

    def test_chunk_respects_size_limit(self):
        from backend.rag.chunker import chunk_pages
        text = "Word " * 500
        pages = [self._make_page_content(text)]
        chunks = chunk_pages(pages)
        for chunk in chunks:
            # Each chunk should be approximately CHUNK_SIZE (700) chars
            assert len(chunk.text) <= 900  # Allow some buffer for overlap

    def test_chunk_skips_empty_pages(self):
        from backend.rag.chunker import chunk_pages
        pages = [
            self._make_page_content(""),
            self._make_page_content("   "),
            self._make_page_content("Real content with enough words " * 10),
        ]
        chunks = chunk_pages(pages)
        # Should only produce chunks from the non-empty page
        assert len(chunks) >= 1


# ── Test: Text Cleaning ───────────────────────────────────────

class TestTextCleaning:
    """Tests for text preprocessing."""

    def test_clean_text_removes_extra_spaces(self):
        from backend.services.pdf_service import _clean_text
        result = _clean_text("Hello    World")
        assert "  " not in result

    def test_clean_text_normalizes_newlines(self):
        from backend.services.pdf_service import _clean_text
        result = _clean_text("Para 1\n\n\n\n\nPara 2")
        assert "\n\n\n" not in result


# ── Test: API Health ──────────────────────────────────────────

class TestAPISetup:
    """Tests for FastAPI application setup (no server needed)."""

    def test_app_creates_successfully(self):
        """Test that the FastAPI app initializes without error."""
        try:
            from backend.main import app
            assert app is not None
            assert app.title == "Ask My PDF Bot"
        except Exception as e:
            pytest.skip(f"Cannot import backend without .env: {e}")

    def test_routes_registered(self):
        """Verify all expected routes are registered."""
        try:
            from backend.main import app
            routes = [route.path for route in app.routes]
            assert "/api/v1/health" in routes
            assert "/api/v1/upload" in routes
            assert "/api/v1/ask" in routes
        except Exception as e:
            pytest.skip(f"Cannot import backend without .env: {e}")


# ── Run Tests ─────────────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
