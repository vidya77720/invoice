from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uvicorn

from app.core.config import settings
from app.api.invoices import router as invoices_router
from app.api.analytics import router as analytics_router
from app.api.vendors import router as vendors_router
from app.api.assistant import router as assistant_router
from app.api.reports import router as reports_router

app = FastAPI(
    title="AI Invoice Intelligence System",
    description="Automated invoice processing with AI extraction and validation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(invoices_router)
app.include_router(analytics_router)
app.include_router(vendors_router)
app.include_router(assistant_router)
app.include_router(reports_router)

# Create directories
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
async def root():
    return {
        "message": "AI Invoice Intelligence System API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/config/categories")
async def get_categories():
    return {"categories": settings.EXPENSE_CATEGORIES}

@app.get("/api/config/statuses")
async def get_statuses():
    return {"statuses": settings.INVOICE_STATUSES}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
