from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.assistant_service import assistant_service

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

class QueryRequest(BaseModel):
    query: str

@router.post("/query")
async def query_assistant(request: QueryRequest):
    """Process natural language query about expenses"""
    try:
        result = assistant_service.process_query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
