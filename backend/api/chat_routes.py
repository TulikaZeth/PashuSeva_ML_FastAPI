# API Routes for Chat Service
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from ..core.base import ChatRequest, ChatResponse
from ..services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat Service"])

# Initialize Chat service
chat_service = ChatService()

@router.post("/ask", response_model=Dict[str, Any])
async def send_message(request: ChatRequest):
    """Send a message to the chat service"""
    try:
        response = await chat_service.process(request)
        return response.dict() if hasattr(response, 'dict') else response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    try:
        conversation = chat_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"conversation_id": conversation_id, "history": conversation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    try:
        success = chat_service.clear_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def chat_health_check():
    """Check Chat service health"""
    try:
        return await chat_service.health_check()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))