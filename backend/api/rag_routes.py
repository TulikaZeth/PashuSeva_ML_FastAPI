# API Routes for RAG Service
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..core.base import RAGRequest, RAGResponse
from ..services.database_service import db_service

router = APIRouter(prefix="/rag", tags=["RAG Service"])

# We'll get the RAG service from main.py
rag_service = None

def set_rag_service(service):
    """Set the RAG service instance from main.py"""
    global rag_service
    rag_service = service

@router.post("/ask", response_model=Dict[str, Any])
async def ask_question(request: RAGRequest):
    """Ask a question about an animal's treatment records"""
    try:
        response = await rag_service.process(request)
        return response.dict() if hasattr(response, 'dict') else response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/animals")
async def list_animals():
    """Get list of all available animals"""
    try:
        return rag_service.get_all_animals()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/animals/{tag_no}")
async def get_animal_info(tag_no: str):
    """Get detailed information about a specific animal"""
    try:
        animal_info = await rag_service.get_animal_info(tag_no)
        if not animal_info:
            raise HTTPException(status_code=404, detail="Animal not found")
        return animal_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def rag_health_check():
    """Check RAG service health"""
    try:
        return await rag_service.health_check()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))