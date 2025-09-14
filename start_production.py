#!/usr/bin/env python3
"""
Production startup script for Veterinary Prescription Analysis API
"""
import os
import sys
import uvicorn
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.core.config import Settings

def setup_logging(settings: Settings):
    """Setup production logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main production startup"""
    settings = Settings()
    
    # Setup logging
    setup_logging(settings)
    logger = logging.getLogger(__name__)
    
    # Validate required environment variables
    required_vars = ["MONGODB_URL", "GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    logger.info("🚀 Starting Veterinary Prescription Analysis API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Host: {settings.host}:{settings.port}")
    logger.info(f"Workers: {settings.max_workers}")
    
    # Production uvicorn configuration
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.max_workers,
        log_level=settings.log_level,
        access_log=True,
        reload=False,  # Never reload in production
        server_header=False,  # Security
        date_header=False,  # Security
    )

if __name__ == "__main__":
    main()