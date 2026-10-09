from fastapi import APIRouter, HTTPException

from app.services.vendor_service import vendor_service

router = APIRouter(prefix="/api/vendors", tags=["vendors"])

@router.get("/")
async def get_vendors():
    """Get all vendors"""
    try:
        vendors = vendor_service.get_all_vendors()
        return vendors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top")
async def get_top_vendors(limit: int = 10):
    """Get top vendors by spending"""
    try:
        vendors = vendor_service.get_top_vendors(limit)
        return vendors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{vendor_name}")
async def get_vendor(vendor_name: str):
    """Get vendor by name"""
    try:
        vendor = vendor_service.get_vendor(vendor_name)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return vendor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{vendor_name}/trends")
async def get_vendor_trends(vendor_name: str):
    """Get spending trends for vendor"""
    try:
        trends = vendor_service.get_vendor_spending_trend(vendor_name)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
