from typing import List, Dict, Optional
from statistics import mean, median, stdev
from datetime import datetime

from app.storage.json_store import invoices_store, anomalies_store
from app.core.config import settings

class AnomalyService:
    """Service for detecting anomalies in invoices"""
    
    def detect_anomalies(self, invoice_data: dict) -> List[str]:
        """Detect anomalies in a single invoice"""
        anomalies = []
        
        # Check for unusually high amount
        if invoice_data.get("total_amount"):
            high_amount_anomaly = self._check_high_amount(invoice_data["total_amount"])
            if high_amount_anomaly:
                anomalies.append(high_amount_anomaly)
        
        # Check for tax mismatch
        if invoice_data.get("subtotal") and invoice_data.get("tax_amount"):
            tax_anomaly = self._check_tax_calculation(
                invoice_data["subtotal"],
                invoice_data["tax_amount"],
                invoice_data.get("total_amount")
            )
            if tax_anomaly:
                anomalies.append(tax_anomaly)
        
        # Check for new/unusual vendor
        if invoice_data.get("vendor_name"):
            vendor_anomaly = self._check_new_vendor(invoice_data["vendor_name"])
            if vendor_anomaly:
                anomalies.append(vendor_anomaly)
        
        # Check for missing important information
        missing_info = self._check_missing_info(invoice_data)
        if missing_info:
            anomalies.extend(missing_info)
        
        # Check for calculation mismatch
        if invoice_data.get("subtotal") and invoice_data.get("total_amount"):
            calc_anomaly = self._check_calculation(invoice_data)
            if calc_anomaly:
                anomalies.append(calc_anomaly)
        
        return anomalies
    
    def _check_high_amount(self, amount: float) -> Optional[str]:
        """Check if amount is unusually high"""
        invoices = invoices_store.read("invoices.json", {})
        amounts = [inv.get("total_amount", 0) for inv in invoices.values() if inv.get("total_amount")]
        
        if len(amounts) < 3:
            return None  # Not enough data to determine
        
        # Calculate statistics
        avg_amount = mean(amounts)
        median_amount = median(amounts)
        
        # Flag if amount is more than 3x the median
        if amount > median_amount * 3:
            return f"Unusually high amount: ₹{amount:,.2f} (median: ₹{median_amount:,.2f})"
        
        return None
    
    def _check_tax_calculation(self, subtotal: float, tax: float, total: Optional[float]) -> Optional[str]:
        """Check if tax calculation seems reasonable"""
        # Calculate tax rate
        if subtotal > 0:
            tax_rate = (tax / subtotal) * 100
            
            # Indian GST rates are typically 5%, 12%, 18%, 28%
            valid_rates = [0, 5, 12, 18, 28]
            
            # Allow small variance (±1%)
            is_valid_rate = any(abs(tax_rate - rate) <= 1 for rate in valid_rates)
            
            if not is_valid_rate:
                return f"Unusual tax rate: {tax_rate:.1f}% (expected: 0%, 5%, 12%, 18%, 28%)"
        
        return None
    
    def _check_new_vendor(self, vendor_name: str) -> Optional[str]:
        """Check if vendor is new or unusual"""
        invoices = invoices_store.read("invoices.json", {})
        vendors = [inv.get("vendor_name") for inv in invoices.values() if inv.get("vendor_name")]
        
        if not vendors:
            return None  # First vendor is not unusual
        
        if vendor_name not in vendors:
            return f"New vendor: {vendor_name}"
        
        return None
    
    def _check_missing_info(self, invoice_data: dict) -> List[str]:
        """Check for missing important information"""
        missing = []
        
        required_fields = [
            ("vendor_name", "Vendor name"),
            ("invoice_number", "Invoice number"),
            ("invoice_date", "Invoice date"),
            ("total_amount", "Total amount")
        ]
        
        for field, display_name in required_fields:
            if not invoice_data.get(field):
                missing.append(f"Missing {display_name}")
        
        return missing
    
    def _check_calculation(self, invoice_data: dict) -> Optional[str]:
        """Check if calculations are consistent"""
        subtotal = invoice_data.get("subtotal")
        tax = invoice_data.get("tax_amount")
        discount = invoice_data.get("discount") or 0
        total = invoice_data.get("total_amount")
        
        if subtotal is not None and tax is not None and total is not None:
            try:
                subtotal = float(subtotal)
                tax = float(tax)
                discount = float(discount)
                total = float(total)
                expected_total = subtotal + tax - discount
                
                # Allow small rounding differences
                if abs(total - expected_total) > 1:
                    return f"Calculation mismatch: Expected ₹{expected_total:,.2f}, Got ₹{total:,.2f}"
            except (ValueError, TypeError):
                pass
        
        return None
    
    def analyze_all_anomalies(self) -> Dict:
        """Analyze all invoices for anomalies"""
        invoices = invoices_store.read("invoices.json", {})
        anomaly_report = {
            "total_invoices": len(invoices),
            "invoices_with_anomalies": 0,
            "anomaly_types": {},
            "anomalies_by_invoice": {}
        }
        
        for inv_id, invoice in invoices.items():
            anomalies = self.detect_anomalies(invoice)
            
            if anomalies:
                anomaly_report["invoices_with_anomalies"] += 1
                anomaly_report["anomalies_by_invoice"][inv_id] = anomalies
                
                # Count anomaly types
                for anomaly in anomalies:
                    anomaly_type = anomaly.split(":")[0].strip()
                    anomaly_report["anomaly_types"][anomaly_type] = \
                        anomaly_report["anomaly_types"].get(anomaly_type, 0) + 1
        
        return anomaly_report
    
    def save_anomaly_report(self, invoice_id: str, anomalies: List[str]):
        """Save anomaly information for an invoice"""
        if anomalies:
            anomalies_store.update("anomalies.json", invoice_id, {
                "invoice_id": invoice_id,
                "anomalies": anomalies,
                "detected_at": datetime.now().isoformat()
            })

anomaly_service = AnomalyService()
