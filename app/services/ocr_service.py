import pytesseract
from PIL import Image
from pathlib import Path
from typing import Optional
import io

from app.core.config import settings

class OCRService:
    """Service for OCR text extraction from images"""
    
    def __init__(self):
        # Configure Tesseract path if provided
        if settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
    
    def extract_text_from_image(self, image_path: Path) -> str:
        """Extract text from image file using Tesseract OCR"""
        try:
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
            
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    def extract_text_from_bytes(self, image_bytes: bytes) -> str:
        """Extract text from image bytes"""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
            
        except Exception as e:
            raise Exception(f"OCR extraction from bytes failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Tesseract OCR is available"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            return False

ocr_service = OCRService()
