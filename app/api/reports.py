from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import Optional

from app.services.report_service import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.post("/monthly")
async def generate_monthly_report(month: Optional[str] = Query(None, description="Month in YYYY-MM format")):
    """Generate monthly report in PDF and Excel formats"""
    try:
        result = report_service.generate_monthly_report(month)
        return {
            "message": "Reports generated successfully",
            "month": result["month"],
            "pdf_path": result["pdf_path"],
            "excel_path": result["excel_path"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/csv")
async def export_csv():
    """Export all invoices to CSV"""
    try:
        csv_path = report_service.generate_csv_export()
        return {
            "message": "CSV export generated successfully",
            "csv_path": str(csv_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
