import io
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Try importing Tesseract dependencies — fully optional
try:
    import pytesseract
    from PIL import Image
    _PYTESSERACT_AVAILABLE = True
except ImportError:
    _PYTESSERACT_AVAILABLE = False
    logger.warning("pytesseract / Pillow not installed — OCR disabled.")

from app.core.config import settings


class OCRService:
    """Service for OCR text extraction from images.
    
    Tesseract is OPTIONAL. If not installed the service returns empty strings
    gracefully so the rest of the pipeline (PyMuPDF + AI heuristic) can continue.
    """

    def __init__(self):
        self._tesseract_ok = False

        if not _PYTESSERACT_AVAILABLE:
            logger.warning("OCRService: pytesseract not available — all OCR calls will return ''.")
            return

        # Configure custom path if set in .env
        if settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH

        # Verify Tesseract binary is reachable
        self._tesseract_ok = self._check_tesseract()
        if not self._tesseract_ok:
            logger.warning(
                "OCRService: Tesseract binary not found in PATH. "
                "Install from https://github.com/UB-Mannheim/tesseract/wiki "
                "or set TESSERACT_PATH in .env. Running without OCR."
            )

    def _check_tesseract(self) -> bool:
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_text_from_image(self, image_path: Path) -> str:
        """Extract text from image file using Tesseract OCR.
        Returns empty string if Tesseract is unavailable instead of raising.
        """
        if not self._tesseract_ok or not _PYTESSERACT_AVAILABLE:
            logger.debug("OCR skipped (Tesseract not available) for %s", image_path)
            return ""
        try:
            image = Image.open(image_path)
            if image.mode != "RGB":
                image = image.convert("RGB")
            return pytesseract.image_to_string(image, lang="eng").strip()
        except Exception as e:
            logger.error("OCR extraction failed for %s: %s", image_path, e)
            return ""

    def extract_text_from_bytes(self, image_bytes: bytes) -> str:
        """Extract text from raw image bytes.
        Returns empty string if Tesseract is unavailable instead of raising.
        """
        if not self._tesseract_ok or not _PYTESSERACT_AVAILABLE:
            logger.debug("OCR skipped (Tesseract not available) — returning empty string.")
            return ""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
            return pytesseract.image_to_string(image, lang="eng").strip()
        except Exception as e:
            logger.error("OCR extraction from bytes failed: %s", e)
            return ""

    def is_available(self) -> bool:
        """Return True only when Tesseract is installed and reachable."""
        return self._tesseract_ok and _PYTESSERACT_AVAILABLE


ocr_service = OCRService()
