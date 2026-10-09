from typing import List, Optional
from difflib import SequenceMatcher

from app.storage.json_store import invoices_store
from app.core.config import settings

class DuplicateService:
    """Service for detecting duplicate invoices"""
    
    def check_duplicate(self, invoice_data: dict) -> dict:
        """Check if invoice is a duplicate"""
        invoices = invoices_store.read("invoices.json", {})
        
        # Skip self-check if updating existing invoice
        invoice_id = invoice_data.get("id")
        
        duplicates = []
        
        for existing_id, existing_invoice in invoices.items():
            if existing_id == invoice_id:
                continue
            
            # Check for exact duplicate (file hash)
            if invoice_data.get("file_hash") == existing_invoice.get("file_hash"):
                duplicates.append({
                    "type": "EXACT_DUPLICATE",
                    "invoice_id": existing_id,
                    "reason": "Same file hash"
                })
                continue
            
            # Check for possible duplicate (vendor + invoice number + date + amount)
            if self._is_possible_duplicate(invoice_data, existing_invoice):
                duplicates.append({
                    "type": "POSSIBLE_DUPLICATE",
                    "invoice_id": existing_id,
                    "reason": "Similar vendor, invoice number, date, and amount"
                })
        
        if not duplicates:
            return {
                "status": "NO_DUPLICATE",
                "duplicates": []
            }
        
        # Determine overall status
        has_exact = any(d["type"] == "EXACT_DUPLICATE" for d in duplicates)
        status = "EXACT_DUPLICATE" if has_exact else "POSSIBLE_DUPLICATE"
        
        return {
            "status": status,
            "duplicates": duplicates
        }
    
    def _is_possible_duplicate(self, invoice1: dict, invoice2: dict) -> bool:
        """Check if two invoices are possibly duplicates"""
        # Check vendor name similarity
        vendor1 = (invoice1.get("vendor_name") or "").lower().strip()
        vendor2 = (invoice2.get("vendor_name") or "").lower().strip()
        
        if vendor1 and vendor2:
            vendor_similarity = SequenceMatcher(None, vendor1, vendor2).ratio()
            if vendor_similarity < 0.8:
                return False
        elif vendor1 != vendor2:
            return False
        
        # Check invoice number
        inv_num1 = (invoice1.get("invoice_number") or "").strip()
        inv_num2 = (invoice2.get("invoice_number") or "").strip()
        
        if inv_num1 and inv_num2:
            if inv_num1 != inv_num2:
                return False
        
        # Check invoice date
        date1 = invoice1.get("invoice_date")
        date2 = invoice2.get("invoice_date")
        
        if date1 and date2:
            if date1 != date2:
                return False
        
        # Check amount (allow small variance)
        amount1 = invoice1.get("total_amount")
        amount2 = invoice2.get("total_amount")
        
        if amount1 and amount2:
            if abs(amount1 - amount2) > 1:  # Allow 1 unit variance
                return False
        
        # If all checks pass, it's a possible duplicate
        return True
    
    def find_all_duplicates(self) -> List[dict]:
        """Find all duplicate invoices in the system"""
        invoices = invoices_store.read("invoices.json", {})
        duplicate_groups = []
        
        # Group by file hash
        hash_groups = {}
        for inv_id, invoice in invoices.items():
            file_hash = invoice.get("file_hash")
            if file_hash:
                if file_hash not in hash_groups:
                    hash_groups[file_hash] = []
                hash_groups[file_hash].append(inv_id)
        
        # Find exact duplicates
        for file_hash, invoice_ids in hash_groups.items():
            if len(invoice_ids) > 1:
                duplicate_groups.append({
                    "type": "EXACT_DUPLICATE",
                    "file_hash": file_hash,
                    "invoice_ids": invoice_ids
                })
        
        return duplicate_groups

duplicate_service = DuplicateService()
