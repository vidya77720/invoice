from typing import Dict, List
from collections import Counter

from app.storage.json_store import invoices_store
from app.core.config import settings

class CategoryService:
    """Service for expense categorization and analysis"""
    
    def get_category_summary(self) -> Dict:
        """Get summary of expenses by category"""
        invoices = invoices_store.read("invoices.json", {})
        
        category_totals = {}
        category_counts = {}
        
        for invoice in invoices.values():
            category = invoice.get("category", "Other")
            amount = invoice.get("total_amount", 0) or 0
            
            if category not in category_totals:
                category_totals[category] = 0
                category_counts[category] = 0
            
            category_totals[category] += amount
            category_counts[category] += 1
        
        return {
            "categories": category_totals,
            "counts": category_counts,
            "total_amount": sum(category_totals.values()),
            "total_invoices": sum(category_counts.values())
        }
    
    def get_category_trends(self, category: str = None) -> Dict:
        """Get spending trends by category"""
        invoices = invoices_store.read("invoices.json", {})
        
        monthly_data = {}
        
        for invoice in invoices.values():
            inv_category = invoice.get("category", "Other")
            if category and inv_category != category:
                continue
            
            invoice_date = invoice.get("invoice_date")
            if not invoice_date:
                continue
            
            # Extract month (YYYY-MM)
            month = invoice_date[:7] if len(invoice_date) >= 7 else invoice_date
            
            amount = invoice.get("total_amount", 0) or 0
            
            if month not in monthly_data:
                monthly_data[month] = 0
            monthly_data[month] += amount
        
        return {
            "category": category or "All",
            "monthly_data": monthly_data
        }
    
    def suggest_category(self, invoice_data: dict) -> str:
        """Suggest category for an invoice (already implemented in AI service)"""
        from app.services.ai_service import ai_service
        return ai_service.categorize_expense(invoice_data)
    
    def get_top_categories(self, limit: int = 5) -> List[Dict]:
        """Get top spending categories"""
        summary = self.get_category_summary()
        
        sorted_categories = sorted(
            summary["categories"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {
                "category": cat,
                "total_amount": amount,
                "count": summary["counts"][cat],
                "percentage": (amount / summary["total_amount"] * 100) if summary["total_amount"] > 0 else 0
            }
            for cat, amount in sorted_categories[:limit]
        ]

category_service = CategoryService()
