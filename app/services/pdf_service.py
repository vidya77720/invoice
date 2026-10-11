import hashlib
import logging
from pathlib import Path
from typing import Optional

import pymupdf  # PyMuPDF

from app.core.config import settings
from app.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)


class PDFService:
    """Service for PDF/image text extraction and processing.

    Strategy (in priority order):
    1. PyMuPDF native text layer  — works for digital PDFs always
    2. Tesseract OCR via ocr_service — only if available AND page text is < 50 chars
    3. Graceful empty string     — never crashes the pipeline
    """

    # ------------------------------------------------------------------ #
    # Core extraction helpers
    # ------------------------------------------------------------------ #

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from a PDF file using PyMuPDF."""
        try:
            doc = pymupdf.open(pdf_path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return text.strip()
        except Exception as e:
            logger.error("PDF text extraction failed for %s: %s", pdf_path, e)
            raise Exception(f"PDF text extraction failed: {e}")

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text from raw PDF bytes using PyMuPDF."""
        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return text.strip()
        except Exception as e:
            logger.error("PDF text extraction from bytes failed: %s", e)
            raise Exception(f"PDF text extraction from bytes failed: {e}")

    def extract_text_with_ocr(self, pdf_path: Path) -> str:
        """Extract text from PDF using PyMuPDF first; fall back to OCR only when
        a page has very little native text AND Tesseract is installed.

        Never raises — worst case returns whatever text PyMuPDF extracted.
        """
        text_parts: list[str] = []
        try:
            doc = pymupdf.open(pdf_path)
            for page in doc:
                page_text = page.get_text().strip()

                # Attempt OCR only if the page looks like a scanned image
                if len(page_text) < 50 and ocr_service.is_available():
                    try:
                        pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                        img_bytes = pix.tobytes("png")
                        ocr_text = ocr_service.extract_text_from_bytes(img_bytes)
                        page_text = ocr_text if ocr_text else page_text
                    except Exception as ocr_err:
                        logger.warning("OCR attempt failed on page, using PyMuPDF text: %s", ocr_err)

                text_parts.append(page_text)
            doc.close()
        except Exception as e:
            logger.error("PDF OCR extraction failed: %s", e)
            # Don't re-raise — return whatever we have so far
        return "\n".join(text_parts).strip()

    # ------------------------------------------------------------------ #
    # Image extraction
    # ------------------------------------------------------------------ #

    def extract_text_from_image_bytes(self, image_bytes: bytes, file_ext: str = "png") -> str:
        """Extract text from image bytes.
        
        1. Try Tesseract OCR (if available).
        2. Try PyMuPDF as image document fallback.
        3. Return '' if both fail — no crash.
        """
        # Primary: Tesseract
        if ocr_service.is_available():
            try:
                result = ocr_service.extract_text_from_bytes(image_bytes)
                if result:
                    return result
            except Exception as e:
                logger.warning("Tesseract image extraction failed: %s", e)

        # Fallback: try opening via PyMuPDF (works for some image formats)
        try:
            doc = pymupdf.open(stream=image_bytes, filetype=file_ext)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            if text.strip():
                return text.strip()
        except Exception as e:
            logger.debug("PyMuPDF image fallback also failed: %s", e)

        return ""

    # ------------------------------------------------------------------ #
    # Utility helpers
    # ------------------------------------------------------------------ #

    def get_page_count(self, pdf_path: Path) -> int:
        """Get number of pages in a PDF."""
        try:
            doc = pymupdf.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return 0

    def is_text_extractable(self, pdf_path: Path) -> bool:
        """Return True if the PDF has a native text layer with >100 chars."""
        try:
            doc = pymupdf.open(pdf_path)
            for page in doc:
                if len(page.get_text().strip()) > 100:
                    doc.close()
                    return True
            doc.close()
            return False
        except Exception:
            return False

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def calculate_bytes_hash(self, file_bytes: bytes) -> str:
        """Calculate SHA-256 hash of raw bytes."""
        return hashlib.sha256(file_bytes).hexdigest()


pdf_service = PDFService()
