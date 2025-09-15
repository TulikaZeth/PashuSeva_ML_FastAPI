# MongoDB Database Service
import asyncio
import logging
from urllib.parse import quote_plus
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from typing import Dict, Any, List, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)

class DatabaseService:
    """MongoDB database service for animal records"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.collection = None
        self.is_connected = False
    
    def _convert_objectid(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string and use tagNo as id"""
        if doc is None:
            return None
        
        # Convert ObjectId to string
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        
        # Use tagNo as the primary identifier
        if "tagNo" in doc:
            doc["id"] = doc["tagNo"]
        
        return doc
    
    def _convert_objectids_list(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert ObjectIds in a list of documents"""
        return [self._convert_objectid(doc) for doc in docs if doc is not None]
        
    async def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            # Use the MongoDB URL directly from settings (already includes password)
            mongodb_url = settings.mongodb_url
            
            # Create client with connection options
            self.client = AsyncIOMotorClient(
                mongodb_url,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                maxPoolSize=10,
                retryWrites=True
            )
            
            # Test the connection
            await self.client.admin.command('ping')
            
            # Get database and collection
            self.database = self.client[settings.mongodb_database]
            self.collection = self.database[settings.mongodb_collection]
            
            self.is_connected = True
            logger.info(f"✓ Connected to MongoDB database: {settings.mongodb_database}")
            logger.info(f"✓ Using collection: {settings.mongodb_collection}")
            
            return True
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("Disconnected from MongoDB")
    
    async def get_animal(self, tag_no: str) -> Optional[Dict[str, Any]]:
        """Get animal record by tag number"""
        if not self.is_connected:
            return None
            
        try:
            result = await self.collection.find_one({"tagNo": tag_no})
            return self._convert_objectid(result)
        except Exception as e:
            logger.error(f"Error fetching animal {tag_no}: {e}")
            return None
    
    async def get_all_animals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all animal records"""
        if not self.is_connected:
            return []
            
        try:
            cursor = self.collection.find().limit(limit)
            animals = await cursor.to_list(length=limit)
            return self._convert_objectids_list(animals)
        except Exception as e:
            logger.error(f"Error fetching animals: {e}")
            return []
    
    async def insert_animal(self, animal_data: Dict[str, Any]) -> bool:
        """Insert a new animal record"""
        if not self.is_connected:
            return False
            
        try:
            result = await self.collection.insert_one(animal_data)
            logger.info(f"Inserted animal with ID: {result.inserted_id}")
            return True
        except Exception as e:
            logger.error(f"Error inserting animal: {e}")
            return False
    
    async def update_animal(self, tag_no: str, update_data: Dict[str, Any]) -> bool:
        """Update animal record"""
        if not self.is_connected:
            return False
            
        try:
            result = await self.collection.update_one(
                {"tagNo": tag_no},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating animal {tag_no}: {e}")
            return False
    
    async def delete_animal(self, tag_no: str) -> bool:
        """Delete animal record"""
        if not self.is_connected:
            return False
            
        try:
            result = await self.collection.delete_one({"tagNo": tag_no})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting animal {tag_no}: {e}")
            return False
    
    async def search_animals(self, query: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """Search animals with query"""
        if not self.is_connected:
            return []
            
        try:
            cursor = self.collection.find(query).limit(limit)
            animals = await cursor.to_list(length=limit)
            return self._convert_objectids_list(animals)
        except Exception as e:
            logger.error(f"Error searching animals: {e}")
            return []
    
    async def count_animals(self) -> int:
        """Get total count of animals"""
        if not self.is_connected:
            return 0
            
        try:
            count = await self.collection.count_documents({})
            return count
        except Exception as e:
            logger.error(f"Error counting animals: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for database connection"""
        try:
            if not self.is_connected:
                return {
                    "status": "disconnected",
                    "database": settings.mongodb_database,
                    "collection": settings.mongodb_collection,
                    "error": "Not connected to MongoDB"
                }
            
            # Test connection
            await self.client.admin.command('ping')
            count = await self.count_animals()
            
            return {
                "status": "connected",
                "database": settings.mongodb_database,
                "collection": settings.mongodb_collection,
                "animal_count": count,
                "connection_healthy": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "database": settings.mongodb_database,
                "collection": settings.mongodb_collection,
                "error": str(e),
                "connection_healthy": False
            }

# Global database service instance
db_service = DatabaseService()