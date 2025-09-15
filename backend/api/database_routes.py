# Database API Routes
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from ..services.database_service import db_service
from ..core.base import AnimalCreateRequest, AnimalUpdateRequest

router = APIRouter(prefix="/database", tags=["Database"])
logger = logging.getLogger(__name__)

@router.get("/health")
async def database_health_check():
    """Check database connection health"""
    try:
        health_status = await db_service.health_check()
        if health_status["status"] == "connected":
            return health_status
        else:
            raise HTTPException(status_code=503, detail=health_status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/animals", response_model=List[Dict[str, Any]])
async def get_all_animals(limit: int = Query(100, ge=1, le=1000)):
    """Get all animals from MongoDB"""
    try:
        logger.info(f"Getting all animals with limit {limit}")
        logger.info(f"Database service connected: {db_service.is_connected}")
        
        if not db_service.is_connected:
            raise HTTPException(status_code=503, detail="Database service not connected")
        
        animals = await db_service.get_all_animals(limit=limit)
        logger.info(f"Successfully retrieved {len(animals)} animals")
        return animals
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching animals: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/animals/{tag_no}")
async def get_animal(tag_no: str):
    """Get specific animal by tag number"""
    try:
        logger.info(f"Getting animal with tag_no: {tag_no}")
        logger.info(f"Database service connected: {db_service.is_connected}")
        
        if not db_service.is_connected:
            raise HTTPException(status_code=503, detail="Database service not connected")
        
        animal = await db_service.get_animal(tag_no)
        if animal:
            logger.info(f"Successfully retrieved animal: {tag_no}")
            return animal
        else:
            logger.warning(f"Animal not found: {tag_no}")
            raise HTTPException(status_code=404, detail="The requested resource was not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching animal {tag_no}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        stats = await db_service.get_stats()
        return {
            "total_animals": stats.get("total_animals", 0),
            "database_status": "connected" if db_service.is_connected else "disconnected",
            "collection": stats.get("collection", "animals"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/animals")
async def create_animal(animal_request: AnimalCreateRequest):
    """Create a new animal record with validated fields"""
    try:
        # Convert Pydantic model to dict and add timestamps
        animal_data = animal_request.dict()
        animal_data["createdAt"] = datetime.now().isoformat()
        animal_data["updatedAt"] = datetime.now().isoformat()
        
        # Initialize default compliance status if not provided
        if not animal_data.get("complianceStatus"):
            animal_data["complianceStatus"] = {
                "status": "OK",
                "lastUpdated": datetime.now().isoformat()
            }
        
        # Add default history entry if not provided
        if not animal_data.get("history"):
            animal_data["history"] = [{
                "date": datetime.now().isoformat(),
                "type": "Registration",
                "details": "Animal registered in the system"
            }]
        
        success = await db_service.insert_animal(animal_data)
        if success:
            return {
                "message": "Animal created successfully", 
                "tagNo": animal_data.get("tagNo"),
                "animalData": {
                    "tagNo": animal_data.get("tagNo"),
                    "breed": animal_data.get("breed"),
                    "gender": animal_data.get("gender"),
                    "farmId": animal_data.get("farmId")
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create animal")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating animal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/animals/{tag_no}")
async def update_animal(tag_no: str, update_request: AnimalUpdateRequest):
    """Update animal record with validated fields"""
    try:
        # Convert Pydantic model to dict and filter out None values
        update_data = {k: v for k, v in update_request.dict().items() if v is not None}
        
        # Add updated timestamp
        update_data["updatedAt"] = datetime.now().isoformat()
        
        success = await db_service.update_animal(tag_no, update_data)
        if success:
            return {
                "message": f"Animal {tag_no} updated successfully",
                "updatedFields": list(update_data.keys())
            }
        else:
            raise HTTPException(status_code=404, detail=f"Animal {tag_no} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating animal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/animals/{tag_no}")
async def delete_animal(tag_no: str):
    """Delete animal record"""
    try:
        success = await db_service.delete_animal(tag_no)
        if success:
            return {"message": f"Animal {tag_no} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Animal {tag_no} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting animal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/animals/search")
async def search_animals(search_criteria: Dict[str, Any]):
    """Search for animals based on criteria"""
    try:
        animals = await db_service.search_animals(search_criteria)
        return {
            "query": search_criteria,
            "count": len(animals),
            "animals": animals
        }
    except Exception as e:
        logger.error(f"Error searching animals: {e}")
        raise HTTPException(status_code=500, detail=str(e))