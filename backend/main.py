"""
Streamlined FastAPI Application for Veterinary Prescription Analysis
Core functionality: RAG, AMU, MRL, Risk Prediction, and Prescription Analysis
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from backend.core.config import settings
from backend.services.rag_service import RAGService
from backend.services.chat_service import ChatService
from backend.agents.amu_tracking_agent import AMUTrackingAgent
from backend.agents.mrl_compliance_agent import MRLComplianceAgent
from backend.agents.risk_prediction_agent import RiskPredictionAgent
from backend.agents.prescription_analyzer_agent import PrescriptionAnalyzerAgent
from backend.services.database_service import db_service
from backend.api import (
    rag_routes, 
    chat_routes,
    prescription_routes,
    risk_routes,
    amu_routes,
    mrl_routes,
    database_routes,
    animal_routes
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Veterinary Prescription Analysis Backend...")
    
    # Initialize core services
    try:
        # Initialize Database service
        db_connected = await db_service.connect()
        if db_connected:
            logger.info("✓ Database Service connected")
        else:
            logger.warning("⚠ Database Service connection failed - continuing without MongoDB")
        
        # Initialize RAG service with database service
        rag_service = RAGService(db_service)
        await rag_service.initialize()
        logger.info("✓ RAG Service initialized")
        
        # Set RAG service in routes
        from backend.api import rag_routes
        rag_routes.set_rag_service(rag_service)
        
        # Initialize Chat service
        chat_service = ChatService()
        logger.info("✓ Chat Service initialized")
        
        # Initialize core agents
        amu_agent = AMUTrackingAgent()
        logger.info("✓ AMU Tracking Agent initialized")
        
        mrl_agent = MRLComplianceAgent()
        logger.info("✓ MRL Compliance Agent initialized")
        
        risk_agent = RiskPredictionAgent()
        logger.info("✓ Risk Prediction Agent initialized")
        
        prescription_agent = PrescriptionAnalyzerAgent()
        logger.info("✓ Prescription Analyzer Agent initialized")
        
        # Set agents in prescription routes
        from backend.api import prescription_routes
        prescription_routes.set_rag_service(rag_service)
        prescription_routes.set_prescription_analyzer(prescription_agent)
        prescription_routes.set_amu_agent(amu_agent)
        prescription_routes.set_mrl_agent(mrl_agent)
        
        # Set services in animal routes
        from backend.api import animal_routes
        animal_routes.set_services(rag_service, chat_service, amu_agent, mrl_agent, risk_agent)
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down services...")
    if db_service.is_connected:
        await db_service.disconnect()
    
    # Shutdown
    logger.info("Shutting down services...")
    # Add cleanup code here if needed

# Create FastAPI app
app = FastAPI(
    title="Veterinary Prescription Analysis API",
    description="Comprehensive veterinary prescription analysis with AMU tracking, MRL compliance, and risk prediction",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware with production settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Restricted origins in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include essential routers only
app.include_router(animal_routes.router)  # New unified animal-centric API
app.include_router(rag_routes.router)
app.include_router(chat_routes.router)
app.include_router(prescription_routes.router)
app.include_router(risk_routes.router)
app.include_router(amu_routes.router)
app.include_router(mrl_routes.router)
app.include_router(database_routes.router)

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Veterinary Prescription Analysis API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "services": [
            "Animal API - Unified tag-based access to all services",
            "RAG Service - Knowledge retrieval",
            "Chat Service - Conversational AI",
            "AMU Agent - Antimicrobial usage tracking",
            "MRL Agent - Maximum residue limit compliance",
            "Risk Prediction - AMR risk assessment",
            "Prescription Analyzer - OCR and NLP analysis"
        ],
        "usage": {
            "animal_overview": "/animal/{tag_no}",
            "rag_analysis": "/animal/{tag_no}/rag",
            "amu_analysis": "/animal/{tag_no}/amu", 
            "mrl_analysis": "/animal/{tag_no}/mrl",
            "amr_analysis": "/animal/{tag_no}/amr",
            "chat": "/animal/{tag_no}/chat",
            "comprehensive": "/animal/{tag_no}/comprehensive"
        }
    }

@app.get("/health")
async def health_check():
    """Global health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "rag_service": "active",
            "chat_service": "active", 
            "amu_agent": "active",
            "mrl_agent": "active",
            "risk_agent": "active",
            "prescription_analyzer": "active"
        }
    }

@app.get("/api/info")
async def api_info():
    """Detailed API information"""
    return {
        "title": "Veterinary Prescription Analysis API",
        "description": "Comprehensive veterinary prescription analysis with AMU tracking, MRL compliance, and risk prediction",
        "version": "2.0.0",
        "endpoints": {
            "animal_unified": "/animal/{tag_no} - Complete animal overview and analysis",
            "animal_rag": "/animal/{tag_no}/rag - Animal-specific RAG analysis",
            "animal_amu": "/animal/{tag_no}/amu - Animal AMU tracking",
            "animal_mrl": "/animal/{tag_no}/mrl - Animal MRL compliance",
            "animal_amr": "/animal/{tag_no}/amr - Animal AMR risk assessment",
            "animal_chat": "/animal/{tag_no}/chat - Animal-specific chat",
            "animal_comprehensive": "/animal/{tag_no}/comprehensive - Full analysis suite",
            "prescription_upload": "/prescription/upload - Upload and analyze prescriptions",
            "database_animals": "/database/animals - Animal database operations",
            "health_checks": "/health - Global health status"
        },
        "features": [
            "OCR text extraction from prescription images",
            "NLP parsing for structured data extraction",
            "AMU guideline compliance checking",
            "MRL violation prediction",
            "Withdrawal period calculation",
            "Risk assessment and scoring",
            "Historical data integration"
        ]
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    import traceback
    error_details = str(exc)
    traceback_str = traceback.format_exc()
    
    logger.error(f"Internal server error: {exc}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Traceback: {traceback_str}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": f"An unexpected error occurred: {error_details}",
            "timestamp": datetime.now().isoformat(),
            "detail": error_details
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8001,
        reload=True
    )