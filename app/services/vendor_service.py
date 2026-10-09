from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

from app.storage.json_store import invoices_store, vendors_store

class VendorService:
    """Service for vendor intelligence and analytics"""
    
    def update_vendor_data(self, invoice_data: dict):
        """Update vendor data based on invoice"""
        vendor_name = invoice_data.get("vendor_name")
        if not vendor_name:
            return
        
        # Get existing vendor data
        vendors = vendors_store.read("vendors.json", {})
        
        if vendor_name not in vendors:
            vendors[vendor_name] = {
                "name": vendor_name,
                "total_invoices": 0,
                "total_spending": 0,
                "first_invoice": None,
                "last_invoice": None,
                "categories": [],
                "average_invoice": 0,
                "invoice_ids": []
            }
        
        vendor = vendors[vendor_name]
        
        # Update metrics
        vendor["total_invoices"] += 1
        vendor["total_spending"] += invoice_data.get("total_amount", 0) or 0
        vendor["invoice_ids"].append(invoice_data["id"])
        
        # Update dates
        invoice_date = invoice_data.get("invoice_date")
        if invoice_date:
            if not vendor["first_invoice"] or invoice_date < vendor["first_invoice"]:
                vendor["first_invoice"] = invoice_date
            if not vendor["last_invoice"] or invoice_date > vendor["last_invoice"]:
                vendor["last_invoice"] = invoice_date
        
        # Update categories
        category = invoice_data.get("category")
        if category and category not in vendor["categories"]:
            vendor["categories"].append(category)
        
        # Calculate average
        vendor["average_invoice"] = vendor["total_spending"] / vendor["total_invoices"]
        
        # Save
        vendors_store.write("vendors.json", vendors)
    
    def get_vendor(self, vendor_name: str) -> Optional[dict]:
        """Get vendor data"""
        vendors = vendors_store.read("vendors.json", {})
        return vendors.get(vendor_name)
    
    def get_all_vendors(self) -> List[dict]:
        """Get all vendors"""
        vendors = vendors_store.read("vendors.json", {})
        return list(vendors.values())
    
    def get_top_vendors(self, limit: int = 10) -> List[dict]:
        """Get top vendors by spending"""
        vendors = self.get_all_vendors()
        
        sorted_vendors = sorted(
            vendors,
            key=lambda x: x.get("total_spending", 0),
            reverse=True
        )
        
        return sorted_vendors[:limit]
    
    def get_vendor_spending_trend(self, vendor_name: str) -> Dict:
        """Get spending trend for a specific vendor"""
        invoices = invoices_store.read("invoices.json", {})
        
        vendor_invoices = [
            inv for inv in invoices.values()
            if inv.get("vendor_name") == vendor_name
        ]
        
        monthly_spending = defaultdict(float)
        
        for invoice in vendor_invoices:
            invoice_date = invoice.get("invoice_date")
            if invoice_date:
                month = invoice_date[:7] if len(invoice_date) >= 7 else invoice_date
                monthly_spending[month] += invoice.get("total_amount", 0) or 0
        
        return {
            "vendor": vendor_name,
            "monthly_spending": dict(monthly_spending),
            "total_invoices": len(vendor_invoices)
        }

vendor_service = VendorService()
