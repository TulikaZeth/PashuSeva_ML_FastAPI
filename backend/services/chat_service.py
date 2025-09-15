# Chat Service Implementation
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..core.base import BaseService, ChatRequest, ChatResponse
from ..core.config import settings

class ChatService(BaseService):
    """General purpose chat service using Gemini"""
    
    def __init__(self):
        super().__init__("chat_service", "1.0.0")
        self.gemini_api_key = settings.gemini_api_key
        self.gemini_model = settings.gemini_model
        self.conversations: Dict[str, List[Dict]] = {}
        
    async def initialize(self) -> bool:
        """Initialize the chat service"""
        try:
            self.is_initialized = True
            self.logger.info("Chat Service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Chat Service: {e}")
            return False
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API for chat"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent"
            headers = {"x-goog-api-key": self.gemini_api_key, "Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 503:
                return "I'm currently overloaded. Please try again in a few moments."
            elif response.status_code != 200:
                return f"I'm having trouble responding right now. Please try again."
            
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            
        except Exception as e:
            self.logger.error(f"Error calling Gemini API: {e}")
            return "I'm sorry, I'm having technical difficulties. Please try again later."
    
    def _build_conversation_prompt(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Build conversation prompt with history"""
        prompt = "You are a helpful AI assistant. Provide clear, concise, and helpful responses.\n\n"
        
        if history:
            prompt += "Conversation History:\n"
            for entry in history[-5:]:  # Keep last 5 exchanges
                prompt += f"Human: {entry.get('user', '')}\n"
                prompt += f"Assistant: {entry.get('assistant', '')}\n\n"
        
        prompt += f"Human: {message}\nAssistant:"
        return prompt
    
    async def process(self, request: ChatRequest) -> ChatResponse:
        """Process chat request"""
        try:
            # Generate conversation ID if not provided
            conversation_id = request.session_id or f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Build prompt with history
            prompt = self._build_conversation_prompt(request.message, request.conversation_history)
            
            # Get response from Gemini
            response_text = await self._call_gemini(prompt)
            
            # Store conversation
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
            
            self.conversations[conversation_id].append({
                "user": request.message,
                "assistant": response_text,
                "timestamp": datetime.now().isoformat()
            })
            
            return ChatResponse(
                success=True,
                message="Chat response generated successfully",
                service_name=self.name,
                timestamp=datetime.now().isoformat(),
                user_message=request.message,
                response=response_text,
                conversation_id=conversation_id
            )
            
        except Exception as e:
            self.logger.error(f"Error processing chat request: {e}")
            return ChatResponse(
                success=False,
                message="Error processing chat request",
                error=str(e),
                service_name=self.name,
                timestamp=datetime.now().isoformat(),
                user_message=request.message,
                response="I'm sorry, I couldn't process your message. Please try again.",
                conversation_id=""
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        return {
            "service": self.name,
            "version": self.version,
            "status": "healthy" if self.is_initialized else "unhealthy",
            "active_conversations": len(self.conversations),
            "gemini_api_configured": bool(self.gemini_api_key)
        }
    
    def get_conversation(self, conversation_id: str) -> Optional[List[Dict]]:
        """Get conversation history"""
        return self.conversations.get(conversation_id)
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False