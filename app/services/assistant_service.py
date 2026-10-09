import httpx
from typing import Dict, Any, List
import json
import re
from datetime import datetime

from app.storage.json_store import invoices_store
from app.core.config import settings

class AssistantService:
    """Service for AI-powered expense assistant"""
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process natural language query about expenses"""
        
        # Analyze query intent using simple pattern matching
        intent = self._analyze_intent(user_query)
        
        # Execute the appropriate query
        result = self._execute_query(intent, user_query)
        
        # Generate natural language response
        response = self._generate_response(intent, result, user_query)
        
        return {
            "query": user_query,
            "intent": intent,
            "result": result,
            "response": response
        }
    
    def _analyze_intent(self, query: str) -> str:
        """Analyze the intent of the user query"""
        query_lower = query.lower()
        
        # Category spending
        if "spend" in query_lower and "software" in query_lower:
            return "category_spending_software"
        elif "spend" in query_lower and "travel" in query_lower:
            return "category_spending_travel"
        elif "spend" in query_lower and "marketing" in query_lower:
            return "category_spending_marketing"
        elif "spend" in query_lower and any(cat in query_lower for cat in ["office", "supplies"]):
            return "category_spending_office"
        elif "spend" in query_lower:
            return "category_spending_general"
        
        # Vendor queries
        elif "highest" in query_lower and "vendor" in query_lower:
            return "highest_vendor"
        elif "vendor" in query_lower and "payment" in query_lower:
            return "vendor_payments"
        
        # Amount-based queries
        elif "above" in query_lower or "over" in query_lower or "greater" in query_lower:
            return "amount_above_threshold"
        elif "below" in query_lower or "under" in query_lower:
            return "amount_below_threshold"
        
        # Status queries
        elif "review" in query_lower or "pending" in query_lower:
            return "review_status"
        elif "approved" in query_lower:
            return "approved_status"
        elif "rejected" in query_lower:
            return "rejected_status"
        
        # Anomaly queries
        elif "anomaly" in query_lower or "unusual" in query_lower:
            return "anomaly_status"
        
        # Duplicate queries
        elif "duplicate" in query_lower:
            return "duplicate_status"
        
        # Total spending
        elif "total" in query_lower and "spend" in query_lower:
            return "total_spending"
        
        # Invoice count
        elif "how many" in query_lower or "count" in query_lower:
            return "invoice_count"
        
        # Date-based queries
        elif "this month" in query_lower:
            return "this_month_spending"
        elif "last month" in query_lower:
            return "last_month_spending"
        
        # Default
        else:
            return "general_query"
    
    def _execute_query(self, intent: str, query: str) -> Dict[str, Any]:
        """Execute the query based on intent"""
        invoices = invoices_store.read("invoices.json", {})
        
        if intent == "category_spending_software":
            return self._get_category_spending(invoices, "Software & Technology")
        elif intent == "category_spending_travel":
            return self._get_category_spending(invoices, "Travel")
        elif intent == "category_spending_marketing":
            return self._get_category_spending(invoices, "Marketing")
        elif intent == "category_spending_office":
            return self._get_category_spending(invoices, "Office Supplies")
        elif intent == "category_spending_general":
            # Try to extract category from query
            for category in settings.EXPENSE_CATEGORIES:
                if category.lower() in query.lower():
                    return self._get_category_spending(invoices, category)
            return {"error": "Could not determine category from query"}
        
        elif intent == "highest_vendor":
            return self._get_highest_vendor(invoices)
        elif intent == "vendor_payments":
            return self._get_vendor_payments(invoices)
        
        elif intent == "amount_above_threshold":
            threshold = self._extract_amount(query)
            return self._get_invoices_above_threshold(invoices, threshold)
        elif intent == "amount_below_threshold":
            threshold = self._extract_amount(query)
            return self._get_invoices_below_threshold(invoices, threshold)
        
        elif intent == "review_status":
            return self._get_invoices_by_status(invoices, "review_required")
        elif intent == "approved_status":
            return self._get_invoices_by_status(invoices, "approved")
        elif intent == "rejected_status":
            return self._get_invoices_by_status(invoices, "rejected")
        
        elif intent == "anomaly_status":
            return self._get_invoices_with_anomalies(invoices)
        elif intent == "duplicate_status":
            return self._get_invoices_with_duplicates(invoices)
        
        elif intent == "total_spending":
            return self._get_total_spending(invoices)
        elif intent == "invoice_count":
            return {"count": len(invoices)}
        
        elif intent == "this_month_spending":
            return self._get_month_spending(invoices, datetime.now().strftime("%Y-%m"))
        elif intent == "last_month_spending":
            # Simple calculation for last month
            current_date = datetime.now()
            if current_date.month == 1:
                last_month = f"{current_date.year - 1}-12"
            else:
                last_month = f"{current_date.year}-{current_date.month - 1:02d}"
            return self._get_month_spending(invoices, last_month)
        
        else:
            return {"error": "Query intent not recognized"}
    
    def _get_category_spending(self, invoices: dict, category: str) -> Dict[str, Any]:
        """Get spending for a specific category"""
        category_invoices = [
            inv for inv in invoices.values()
            if inv.get("category") == category
        ]
        
        total = sum(inv.get("total_amount", 0) or 0 for inv in category_invoices)
        
        return {
            "category": category,
            "total_spending": total,
            "invoice_count": len(category_invoices),
            "invoices": category_invoices
        }
    
    def _get_highest_vendor(self, invoices: dict) -> Dict[str, Any]:
        """Get vendor with highest total spending"""
        vendor_totals = {}
        
        for invoice in invoices.values():
            vendor = invoice.get("vendor_name", "Unknown")
            amount = invoice.get("total_amount", 0) or 0
            
            if vendor not in vendor_totals:
                vendor_totals[vendor] = 0
            vendor_totals[vendor] += amount
        
        if not vendor_totals:
            return {"error": "No vendor data available"}
        
        highest_vendor = max(vendor_totals.items(), key=lambda x: x[1])
        
        return {
            "vendor": highest_vendor[0],
            "total_spending": highest_vendor[1],
            "invoice_count": len([inv for inv in invoices.values() if inv.get("vendor_name") == highest_vendor[0]])
        }
    
    def _extract_amount(self, query: str) -> float:
        """Extract amount from query"""
        # Look for patterns like "₹1 lakh", "100000", "1,00,000", etc.
        patterns = [
            r'₹?([\d,]+(?:\.\d+)?)\s*lakh',
            r'₹?([\d,]+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                amount_str = match.group(1).replace(',', '')
                amount = float(amount_str)
                
                # Convert lakh to actual number
                if "lakh" in query.lower():
                    amount *= 100000
                
                return amount
        
        return 0
    
    def _get_invoices_above_threshold(self, invoices: dict, threshold: float) -> Dict[str, Any]:
        """Get invoices above a threshold amount"""
        if threshold == 0:
            return {"error": "Could not extract threshold from query"}
        
        above_invoices = [
            inv for inv in invoices.values()
            if (inv.get("total_amount", 0) or 0) > threshold
        ]
        
        return {
            "threshold": threshold,
            "count": len(above_invoices),
            "invoices": above_invoices
        }
    
    def _get_invoices_below_threshold(self, invoices: dict, threshold: float) -> Dict[str, Any]:
        """Get invoices below a threshold amount"""
        if threshold == 0:
            return {"error": "Could not extract threshold from query"}
        
        below_invoices = [
            inv for inv in invoices.values()
            if (inv.get("total_amount", 0) or 0) < threshold
        ]
        
        return {
            "threshold": threshold,
            "count": len(below_invoices),
            "invoices": below_invoices
        }
    
    def _get_invoices_by_status(self, invoices: dict, status: str) -> Dict[str, Any]:
        """Get invoices by status"""
        status_invoices = [
            inv for inv in invoices.values()
            if inv.get("status") == status
        ]
        
        return {
            "status": status,
            "count": len(status_invoices),
            "invoices": status_invoices
        }
    
    def _get_invoices_with_anomalies(self, invoices: dict) -> Dict[str, Any]:
        """Get invoices with anomalies"""
        anomaly_invoices = [
            inv for inv in invoices.values()
            if inv.get("anomaly_flags")
        ]
        
        return {
            "count": len(anomaly_invoices),
            "invoices": anomaly_invoices
        }
    
    def _get_invoices_with_duplicates(self, invoices: dict) -> Dict[str, Any]:
        """Get invoices marked as duplicates"""
        duplicate_invoices = [
            inv for inv in invoices.values()
            if inv.get("duplicate_status") in ["POSSIBLE_DUPLICATE", "EXACT_DUPLICATE"]
        ]
        
        return {
            "count": len(duplicate_invoices),
            "invoices": duplicate_invoices
        }
    
    def _get_total_spending(self, invoices: dict) -> Dict[str, Any]:
        """Get total spending across all invoices"""
        total = sum(inv.get("total_amount", 0) or 0 for inv in invoices.values())
        
        return {
            "total_spending": total,
            "invoice_count": len(invoices)
        }
    
    def _get_month_spending(self, invoices: dict, month: str) -> Dict[str, Any]:
        """Get spending for a specific month (YYYY-MM format)"""
        month_invoices = [
            inv for inv in invoices.values()
            if inv.get("invoice_date", "").startswith(month)
        ]
        
        total = sum(inv.get("total_amount", 0) or 0 for inv in month_invoices)
        
        return {
            "month": month,
            "total_spending": total,
            "invoice_count": len(month_invoices)
        }
    
    def _generate_response(self, intent: str, result: Dict[str, Any], query: str) -> str:
        """Generate natural language response"""
        if "error" in result:
            return f"I couldn't process that query: {result['error']}"
        
        # Handle empty results
        if not invoices_store.read("invoices.json", {}):
            return "I don't have any invoice data yet. Please upload some invoices first."
        
        if intent == "category_spending_software":
            if result['invoice_count'] == 0:
                return "You haven't spent anything on software yet."
            return f"You spent ₹{result['total_spending']:,.2f} on software ({result['invoice_count']} invoices)."
        elif intent == "category_spending_travel":
            if result['invoice_count'] == 0:
                return "You haven't spent anything on travel yet."
            return f"You spent ₹{result['total_spending']:,.2f} on travel ({result['invoice_count']} invoices)."
        elif intent == "category_spending_general":
            if result['invoice_count'] == 0:
                return f"You haven't spent anything on {result['category']} yet."
            return f"You spent ₹{result['total_spending']:,.2f} on {result['category']} ({result['invoice_count']} invoices)."
        
        elif intent == "highest_vendor":
            return f"{result['vendor']} received the highest payment: ₹{result['total_spending']:,.2f} ({result['invoice_count']} invoices)."
        
        elif intent == "amount_above_threshold":
            return f"There are {result['count']} invoices above ₹{result['threshold']:,.2f}."
        elif intent == "amount_below_threshold":
            return f"There are {result['count']} invoices below ₹{result['threshold']:,.2f}."
        
        elif intent == "review_status":
            return f"There are {result['count']} invoices requiring review."
        elif intent == "approved_status":
            return f"There are {result['count']} approved invoices."
        elif intent == "rejected_status":
            return f"There are {result['count']} rejected invoices."
        
        elif intent == "anomaly_status":
            return f"There are {result['count']} invoices with potential anomalies."
        elif intent == "duplicate_status":
            return f"There are {result['count']} invoices marked as potential duplicates."
        
        elif intent == "total_spending":
            if result['invoice_count'] == 0:
                return "You don't have any invoices yet."
            return f"Total spending across all invoices: ₹{result['total_spending']:,.2f} ({result['invoice_count']} invoices)."
        elif intent == "invoice_count":
            return f"You have {result['count']} invoices in the system."
        
        elif intent == "this_month_spending":
            if result['invoice_count'] == 0:
                return "You haven't had any invoices this month yet."
            return f"This month's spending: ₹{result['total_spending']:,.2f} ({result['invoice_count']} invoices)."
        elif intent == "last_month_spending":
            if result['invoice_count'] == 0:
                return "You didn't have any invoices last month."
            return f"Last month's spending: ₹{result['total_spending']:,.2f} ({result['invoice_count']} invoices)."
        
        else:
            return "I processed your query. Here are the results."
    
    def close(self):
        """Close HTTP client"""
        self.client.close()

assistant_service = AssistantService()
