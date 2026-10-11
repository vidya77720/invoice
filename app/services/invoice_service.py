from pathlib import Path
from typing import Optional, List, Tuple
import uuid
import shutil
from datetime import datetime, timedelta

from app.core.config import settings
from app.storage.json_store import invoices_store, processing_jobs_store
from app.services.pdf_service import pdf_service
from app.services.ocr_service import ocr_service
from app.services.ai_service import ai_service
from app.services.validation_service import validation_service
from app.services.duplicate_service import duplicate_service
from app.services.anomaly_service import anomaly_service
from app.services.vendor_service import vendor_service

class InvoiceService:
    """Service for invoice file management and basic processing"""
    
    def validate_file(self, filename: str, file_size: int, file_bytes: bytes) -> Tuple[bool, str]:
        """Validate uploaded file"""
        # Check file extension
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            return (False, f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}")
        
        # Check file size
        if file_size > settings.MAX_FILE_SIZE:
            return (False, f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB")
        
        # Check if file is not empty
        if file_size == 0:
            return (False, "File is empty")
        
        return (True, "Valid")
    
    def generate_invoice_id(self) -> str:
        """Generate unique invoice ID"""
        return f"INV-{uuid.uuid4().hex[:8].upper()}"
    
    def generate_filename(self, original_filename: str) -> str:
        """Generate safe random filename"""
        ext = original_filename.split('.')[-1] if '.' in original_filename else 'pdf'
        return f"{uuid.uuid4().hex}.{ext}"
    
    def save_uploaded_file(self, file_bytes: bytes, original_filename: str) -> Tuple[Path, str]:
        """Save uploaded file to uploads directory"""
        filename = self.generate_filename(original_filename)
        file_path = settings.UPLOAD_DIR / filename
        
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        
        return (file_path, filename)
    
    def extract_text(self, file_path: Path, file_ext: str) -> str:
        """Extract text from invoice file.

        PDF  → PyMuPDF native text layer; OCR fallback only if Tesseract is installed.
        Image → Tesseract OCR if available; otherwise return '' (AI heuristic will handle it).
        Never raises — returns at minimum an empty string.
        """
        try:
            if file_ext == 'pdf':
                # Always works — PyMuPDF handles digital PDFs without Tesseract
                return pdf_service.extract_text_with_ocr(file_path)
            else:
                # Image file: try OCR first, else attempt PyMuPDF image read
                if ocr_service.is_available():
                    text = ocr_service.extract_text_from_image(file_path)
                    if text:
                        return text
                # PyMuPDF can sometimes read embedded text in image-type docs
                try:
                    doc = __import__('pymupdf').open(str(file_path))
                    text = "".join(page.get_text() for page in doc)
                    doc.close()
                    if text.strip():
                        return text.strip()
                except Exception:
                    pass
                # Return filename hint so AI heuristic at least has context
                return f"[Image invoice: {file_path.name}]"
        except Exception as e:
            # Log but never crash — let AI service handle with minimal text
            import logging
            logging.getLogger(__name__).error("Text extraction failed: %s", e)
            return f"[Extraction error: {file_path.name}]"

    
    def create_invoice_record(self, file_path: Path, file_name: str, file_size: int, extracted_text: str) -> dict:
        """Create initial invoice record"""
        invoice_id = self.generate_invoice_id()
        file_hash = pdf_service.calculate_file_hash(file_path)
        
        invoice_data = {
            "id": invoice_id,
            "file_path": str(file_path),
            "file_hash": file_hash,
            "file_name": file_name,
            "file_size": file_size,
            "extracted_text": extracted_text,
            "vendor_name": None,
            "vendor_address": None,
            "gstin": None,
            "invoice_number": None,
            "invoice_date": None,
            "due_date": None,
            "currency": "INR",
            "subtotal": None,
            "discount": 0,
            "tax_amount": None,
            "total_amount": None,
            "line_items": [],
            "category": None,
            "confidence_score": 0.0,
            "status": "processing",
            "duplicate_status": "NO_DUPLICATE",
            "anomaly_flags": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Save to storage
        invoices_store.update("invoices.json", invoice_id, invoice_data)
        
        # Track processing job
        processing_jobs_store.update("processing_jobs.json", invoice_id, {
            "job_id": invoice_id,
            "file_name": file_name,
            "status": "processing",
            "created_at": datetime.now().isoformat()
        })
        
        return invoice_data
    
    def get_invoice(self, invoice_id: str) -> Optional[dict]:
        """Get invoice by ID"""
        invoices = invoices_store.read("invoices.json", {})
        return invoices.get(invoice_id)
    
    def get_all_invoices(self) -> List[dict]:
        """Get all invoices"""
        invoices = invoices_store.read("invoices.json", {})
        return list(invoices.values())
    
    def update_invoice(self, invoice_id: str, updates: dict) -> Optional[dict]:
        """Update invoice"""
        invoices = invoices_store.read("invoices.json", {})
        
        if invoice_id not in invoices:
            return None
        
        invoice = invoices[invoice_id]
        invoice.update(updates)
        invoice["updated_at"] = datetime.now().isoformat()
        
        invoices_store.write("invoices.json", invoices)
        return invoice
    
    def delete_invoice(self, invoice_id: str) -> bool:
        """Delete invoice"""
        invoices = invoices_store.read("invoices.json", {})
        
        if invoice_id not in invoices:
            return False
        
        # Delete file
        try:
            file_path = Path(invoices[invoice_id]["file_path"])
            if file_path.exists():
                file_path.unlink()
        except:
            pass
        
        # Delete from storage
        del invoices[invoice_id]
        invoices_store.write("invoices.json", invoices)
        
        return True
    
    def process_invoice_with_ai(self, invoice_id: str) -> dict:
        """Process invoice with AI extraction and validation"""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            raise Exception("Invoice not found")
        
        # Extract data using AI — pass file_path so Gemini Vision can handle scanned PDFs
        extracted_data = ai_service.extract_invoice_data(
            invoice["extracted_text"],
            file_path=invoice.get("file_path")
        )
        
        # Update invoice with extracted data
        updates = {
            "vendor_name": extracted_data.get("vendor_name"),
            "vendor_address": extracted_data.get("vendor_address"),
            "gstin": extracted_data.get("gstin"),
            "invoice_number": extracted_data.get("invoice_number"),
            "invoice_date": extracted_data.get("invoice_date"),
            "due_date": extracted_data.get("due_date"),
            "currency": extracted_data.get("currency", "INR"),
            "subtotal": extracted_data.get("subtotal"),
            "discount": extracted_data.get("discount") or 0,
            "tax_amount": extracted_data.get("tax_amount"),
            "total_amount": extracted_data.get("total_amount"),
            "line_items": extracted_data.get("line_items", [])
        }
        
        # Categorize expense
        category = ai_service.categorize_expense(extracted_data)
        updates["category"] = category
        
        # Validate
        validation = validation_service.validate_invoice(updates)
        
        # Calculate confidence score
        updates["confidence_score"] = validation_service._calculate_confidence_score(
            updates, validation.errors, validation.warnings
        )
        
        # Check for duplicates
        duplicate_check = duplicate_service.check_duplicate(updates)
        updates["duplicate_status"] = duplicate_check["status"]
        
        # Detect anomalies
        anomalies = anomaly_service.detect_anomalies(updates)
        updates["anomaly_flags"] = anomalies + validation.warnings
        
        # Save anomaly report
        if anomalies:
            anomaly_service.save_anomaly_report(invoice_id, anomalies)
        
        # Set status based on validation and anomalies
        if validation.is_valid and updates["confidence_score"] >= 0.8 and not anomalies:
            updates["status"] = "review_required"  # Still need human review
        else:
            updates["status"] = "review_required"
        
        # Archive file to processed directory
        try:
            original_path = Path(invoice["file_path"])
            if original_path.exists():
                processed_path = settings.PROCESSED_DIR / invoice["file_name"]
                shutil.copy2(original_path, processed_path)
                updates["processed_file_path"] = str(processed_path)
        except Exception:
            pass

        # Update invoice
        updated_invoice = self.update_invoice(invoice_id, updates)
        
        # Update vendor data
        if updated_invoice.get("vendor_name"):
            vendor_service.update_vendor_data(updated_invoice)
        
        # Mark job complete
        processing_jobs_store.update("processing_jobs.json", invoice_id, {
            "job_id": invoice_id,
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        })
        
        return updated_invoice

invoice_service = InvoiceService()
