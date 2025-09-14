# Configuration Management
import os
from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional

class Settings(BaseSettings):
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # API Settings
    api_title: str = "Veterinary Prescription Analysis API"
    api_description: str = "Comprehensive veterinary prescription analysis with AMU tracking, MRL compliance, and risk prediction"
    api_version: str = "2.0.0"
    host: str = "0.0.0.0"
    port: int = 8001
    
    # Security Settings
    secret_key: str = os.getenv("SECRET_KEY", "change-this-in-production")
    cors_origins: list = ["*"] if environment == "development" else []
    
    # Database Settings
    csv_data_path: str = "data/animal_records_with_questions.csv"
    
    # MongoDB Settings - Use environment variables in production
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "veterinary_db") 
    mongodb_collection: str = os.getenv("MONGODB_COLLECTION", "animals")
    
    # AI Model Settings - Use environment variables for API keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = "gemini-1.5-flash"
    
    # RAG Settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 400
    chunk_overlap: int = 50
    retrieval_k: int = 5
    
    # Logging Settings
    log_level: str = os.getenv("LOG_LEVEL", "info")
    log_file: str = "logs/app.log"
    
    # Performance Settings
    max_workers: int = int(os.getenv("MAX_WORKERS", "4"))
    request_timeout: int = 300
    
    # Service Settings - Core services only for production
    enable_rag_service: bool = True
    enable_chat_service: bool = True
    
    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}

# Global settings instance
settings = Settings()

# Model configurations - Simplified for production
MODEL_CONFIGS = {
    "rag_service": {
        "name": "RAG Service",
        "description": "Animal treatment records retrieval and Q&A",
        "enabled": settings.enable_rag_service,
        "version": "2.0.0"
    },
    "chat_service": {
        "name": "Chat Service", 
        "description": "General purpose conversational AI",
        "enabled": settings.enable_chat_service,
        "version": "2.0.0"
    },
    "animal_api": {
        "name": "Animal-Centric API",
        "description": "Unified animal-based access to all services",
        "enabled": True,
        "version": "2.0.0"
    }
}

# API endpoint configurations - Updated for animal-centric API
API_ROUTES = {
    "animal": "/animal",
    "rag": "/rag", 
    "chat": "/chat",
    "prescription": "/prescription",
    "amu": "/api/v1/amu",
    "mrl": "/api/v1/mrl",
    "risk": "/risk",
    "database": "/database",
    "health": "/health",
    "docs": "/docs"
}