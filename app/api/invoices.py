from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

from app.services.invoice_service import invoice_service
from app.schemas.invoice import InvoiceResponse

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

class InvoiceUpdateRequest(BaseModel):
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    gstin: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    category: Optional[str] = None
    status: Optional[str] = None

@router.post("/upload")
async def upload_invoice(file: UploadFile = File(...)):
    """Upload and process invoice"""
    try:
        # Read file content
        file_bytes = await file.read()
        file_size = len(file_bytes)
        
        # Validate file
        is_valid, message = invoice_service.validate_file(file.filename, file_size, file_bytes)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Save file
        file_path, filename = invoice_service.save_uploaded_file(file_bytes, file.filename)
        
        # Extract text
        file_ext = filename.split('.')[-1].lower()
        extracted_text = invoice_service.extract_text(file_path, file_ext)
        
        # Create invoice record
        invoice_data = invoice_service.create_invoice_record(
            file_path, filename, file_size, extracted_text
        )
        
        # Process with AI
        try:
            processed_invoice = invoice_service.process_invoice_with_ai(invoice_data["id"])
            return {
                "message": "Invoice uploaded and processed successfully",
                "invoice": processed_invoice
            }
        except Exception as ai_error:
            # If AI processing fails, still return the basic invoice
            return {
                "message": "Invoice uploaded successfully (AI processing failed)",
                "invoice": invoice_data,
                "warning": f"AI processing failed: {str(ai_error)}"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[InvoiceResponse])
async def get_invoices():
    """Get all invoices"""
    try:
        invoices = invoice_service.get_all_invoices()
        return invoices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str):
    """Get invoice by ID"""
    try:
        invoice = invoice_service.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{invoice_id}")
async def update_invoice(invoice_id: str, updates: InvoiceUpdateRequest):
    """Update invoice"""
    try:
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        invoice = invoice_service.update_invoice(invoice_id, update_dict)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return {"message": "Invoice updated successfully", "invoice": invoice}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str):
    """Delete invoice"""
    try:
        success = invoice_service.delete_invoice(invoice_id)
        if not success:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return {"message": "Invoice deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{invoice_id}/approve")
async def approve_invoice(invoice_id: str):
    """Approve invoice"""
    try:
        invoice = invoice_service.update_invoice(invoice_id, {"status": "approved"})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return {"message": "Invoice approved successfully", "invoice": invoice}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{invoice_id}/reject")
async def reject_invoice(invoice_id: str):
    """Reject invoice"""
    try:
        invoice = invoice_service.update_invoice(invoice_id, {"status": "rejected"})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        return {"message": "Invoice rejected successfully", "invoice": invoice}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
