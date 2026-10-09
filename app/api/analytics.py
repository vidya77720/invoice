from fastapi import APIRouter, HTTPException

from app.services.category_service import category_service
from app.services.vendor_service import vendor_service
from app.services.anomaly_service import anomaly_service
from app.services.duplicate_service import duplicate_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/summary")
async def get_analytics_summary():
    """Get overall analytics summary"""
    try:
        category_summary = category_service.get_category_summary()
        vendors = vendor_service.get_all_vendors()
        anomaly_report = anomaly_service.analyze_all_anomalies()
        duplicates = duplicate_service.find_all_duplicates()
        
        return {
            "categories": category_summary,
            "total_vendors": len(vendors),
            "anomalies": anomaly_report,
            "duplicates": len(duplicates)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_category_analytics():
    """Get category analytics"""
    try:
        summary = category_service.get_category_summary()
        top_categories = category_service.get_top_categories()
        trends = category_service.get_category_trends()
        
        return {
            "summary": summary,
            "top_categories": top_categories,
            "trends": trends
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories/{category}/trends")
async def get_category_trends(category: str):
    """Get trends for specific category"""
    try:
        trends = category_service.get_category_trends(category)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
