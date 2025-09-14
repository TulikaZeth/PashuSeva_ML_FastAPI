#!/usr/bin/env python3
"""
Test MongoDB connection with the current configuration
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.services.database_service import DatabaseService
from backend.core.config import Settings

async def test_mongodb_connection():
    """Test MongoDB connection"""
    print("🔍 Testing MongoDB Connection")
    print("=" * 50)
    
    # Check environment variables
    mongodb_url = os.getenv("MONGODB_URL")
    print(f"MONGODB_URL: {mongodb_url[:50]}...")
    
    # Check settings
    settings = Settings()
    print(f"Settings MongoDB URL: {settings.mongodb_url[:50]}...")
    print(f"Settings Database: {settings.mongodb_database}")
    print(f"Settings Collection: {settings.mongodb_collection}")
    
    print("\n🔗 Attempting Connection...")
    
    # Create database service
    db_service = DatabaseService()
    
    try:
        # Try to connect
        success = await db_service.connect()
        
        if success:
            print("✅ MongoDB connection successful!")
            print(f"✅ Connected to database: {settings.mongodb_database}")
            print(f"✅ Using collection: {settings.mongodb_collection}")
            
            # Test health check
            print("\n🏥 Testing health check...")
            health = await db_service.health_check()
            print(f"Health status: {health}")
            
            # Test count
            print("\n🔢 Testing count...")
            count = await db_service.count_animals()
            print(f"Animal count: {count}")
            
            # Test getting a few animals
            if count > 0:
                print("\n🐄 Testing get animals...")
                animals = await db_service.get_all_animals(limit=3)
                print(f"Retrieved {len(animals)} animals")
                for animal in animals:
                    print(f"  - {animal.get('tagNo', 'Unknown')} ({animal.get('species', 'Unknown')})")
            
        else:
            print("❌ MongoDB connection failed!")
            
    except Exception as e:
        print(f"❌ Error during connection test: {e}")
        
    finally:
        if db_service.is_connected:
            await db_service.disconnect()
            print("\n🔒 Disconnected from MongoDB")

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection())