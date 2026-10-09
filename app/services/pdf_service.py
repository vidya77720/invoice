import pymupdf  # PyMuPDF
from pathlib import Path
from typing import Optional
import hashlib

from app.core.config import settings
from app.services.ocr_service import ocr_service

class PDFService:
    """Service for PDF text extraction and processing"""
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            doc = pymupdf.open(pdf_path)
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            return text.strip()
            
        except Exception as e:
            raise Exception(f"PDF text extraction failed: {str(e)}")
    
    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            return text.strip()
            
        except Exception as e:
            raise Exception(f"PDF text extraction from bytes failed: {str(e)}")
    
    def extract_text_with_ocr(self, pdf_path: Path) -> str:
        """Extract text from PDF using OCR if needed"""
        try:
            doc = pymupdf.open(pdf_path)
            text = ""
            
            for page_num, page in enumerate(doc):
                # Try regular text extraction first
                page_text = page.get_text()
                
                # If page has very little text, use OCR
                if len(page_text.strip()) < 50:
                    # Render page to image
                    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                    img_bytes = pix.tobytes("png")
                    
                    # Use OCR
                    page_text = ocr_service.extract_text_from_bytes(img_bytes)
                
                text += page_text
            
            doc.close()
            return text.strip()
            
        except Exception as e:
            raise Exception(f"PDF OCR extraction failed: {str(e)}")
    
    def get_page_count(self, pdf_path: Path) -> int:
        """Get number of pages in PDF"""
        try:
            doc = pymupdf.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except:
            return 0
    
    def is_text_extractable(self, pdf_path: Path) -> bool:
        """Check if PDF has extractable text"""
        try:
            doc = pymupdf.open(pdf_path)
            for page in doc:
                text = page.get_text()
                if len(text.strip()) > 100:
                    doc.close()
                    return True
            doc.close()
            return False
        except:
            return False
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def calculate_bytes_hash(self, file_bytes: bytes) -> str:
        """Calculate SHA-256 hash of bytes"""
        sha256_hash = hashlib.sha256()
        sha256_hash.update(file_bytes)
        return sha256_hash.hexdigest()

pdf_service = PDFService()
