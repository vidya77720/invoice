from typing import List, Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime
import re

from app.schemas.invoice import InvoiceValidation

class ValidationService:
    """Service for validating invoice data"""
    
    def validate_invoice(self, invoice_data: dict) -> InvoiceValidation:
        """Validate invoice data and return validation result"""
        errors = []
        warnings = []
        
        # Required fields validation
        if not invoice_data.get("vendor_name"):
            errors.append("Vendor name is required")
        
        if not invoice_data.get("invoice_number"):
            errors.append("Invoice number is required")
        
        if not invoice_data.get("invoice_date"):
            errors.append("Invoice date is required")
        
        # Amount validation
        total_amount = invoice_data.get("total_amount")
        subtotal = invoice_data.get("subtotal")
        tax_amount = invoice_data.get("tax_amount")
        discount = invoice_data.get("discount", 0)
        
        if total_amount is None:
            errors.append("Total amount is required")
        elif total_amount <= 0:
            errors.append("Total amount must be greater than 0")
        
        # Validate calculation consistency
        if subtotal is not None and tax_amount is not None:
            expected_total = subtotal + tax_amount - (discount or 0)
            if total_amount is not None:
                # Allow small rounding differences
                if abs(total_amount - expected_total) > 1:
                    warnings.append(f"Amount calculation mismatch: Expected {expected_total}, Got {total_amount}")
        
        # Date validation
        invoice_date = invoice_data.get("invoice_date")
        if invoice_date:
            try:
                if isinstance(invoice_date, str):
                    datetime.strptime(invoice_date, "%Y-%m-%d")
            except ValueError:
                errors.append("Invalid invoice date format. Use YYYY-MM-DD")
        
        due_date = invoice_data.get("due_date")
        if due_date:
            try:
                if isinstance(due_date, str):
                    datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                errors.append("Invalid due date format. Use YYYY-MM-DD")
        
        # GSTIN validation (Indian GST format)
        gstin = invoice_data.get("gstin")
        if gstin:
            if not self._validate_gstin(gstin):
                warnings.append("GSTIN format may be invalid")
        
        # Currency validation
        currency = invoice_data.get("currency")
        if currency and currency not in ["INR", "USD", "EUR", "GBP"]:
            warnings.append(f"Unusual currency: {currency}")
        
        # Confidence scoring
        confidence_score = self._calculate_confidence_score(invoice_data, errors, warnings)
        
        # Determine overall validity
        is_valid = len(errors) == 0
        
        return InvoiceValidation(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_gstin(self, gstin: str) -> bool:
        """Validate Indian GSTIN format"""
        # GSTIN format: 2 digits (state code) + 10 characters (PAN) + 1 digit + 1 character + 1 digit
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
        return bool(re.match(pattern, gstin.upper()))
    
    def _calculate_confidence_score(self, invoice_data: dict, errors: List[str], warnings: List[str]) -> float:
        """Calculate confidence score based on data completeness"""
        score = 1.0
        
        # Deduct for missing fields
        if not invoice_data.get("vendor_name"):
            score -= 0.2
        if not invoice_data.get("invoice_number"):
            score -= 0.15
        if not invoice_data.get("invoice_date"):
            score -= 0.1
        if not invoice_data.get("total_amount"):
            score -= 0.2
        if not invoice_data.get("line_items"):
            score -= 0.1
        
        # Deduct for errors and warnings
        score -= len(errors) * 0.1
        score -= len(warnings) * 0.05
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def validate_amount_calculation(self, subtotal: Optional[float], tax: Optional[float], 
                                   discount: Optional[float], total: Optional[float]) -> bool:
        """Validate that total = subtotal + tax - discount"""
        if None in [subtotal, tax, total]:
            return True  # Can't validate if values are missing
        
        discount = discount or 0
        expected_total = subtotal + tax - discount
        
        # Allow small rounding differences (up to 1 currency unit)
        return abs(total - expected_total) <= 1.0

validation_service = ValidationService()
