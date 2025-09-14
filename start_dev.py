#!/usr/bin/env python3
"""
Development server for easier testing - runs on localhost:8001
"""
import os
import sys
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Start development server on localhost for easier testing"""
    print("🚀 Starting Development Server for Testing")
    print("📍 Server will be available at: http://localhost:8001")
    print("📖 API Documentation: http://localhost:8001/docs")
    print("🔗 Interactive API Explorer: http://localhost:8001/redoc")
    print("\n🔧 Available Animal API Endpoints:")
    print("   • GET  /animal/{tag_no}               - Animal overview")
    print("   • GET  /animal/{tag_no}/rag           - RAG analysis")
    print("   • GET  /animal/{tag_no}/amu           - AMU tracking")
    print("   • GET  /animal/{tag_no}/mrl           - MRL compliance")
    print("   • GET  /animal/{tag_no}/amr           - AMR risk prediction")
    print("   • POST /animal/{tag_no}/chat          - Chat with context")
    print("   • GET  /animal/{tag_no}/comprehensive - Complete analysis")
    print("\n📝 Example: http://localhost:8001/animal/105319726733")
    print("\n" + "="*60)
    
    # Single worker development configuration
    uvicorn.run(
        "backend.main:app",
        host="localhost",  # Use localhost instead of 0.0.0.0
        port=8001,
        workers=1,         # Single worker for development
        log_level="info",
        access_log=True,
        reload=False,
        server_header=False,
        date_header=False,
    )

if __name__ == "__main__":
    main()