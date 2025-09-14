# AMU Tracking Agent API Routes
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from ..core.base import AMUTrackingRequest, AMUTrackingResponse
from ..agents.amu_tracking_agent import AMUTrackingAgent

router = APIRouter(prefix="/api/v1/amu", tags=["AMU Tracking"])
logger = logging.getLogger(__name__)

# Initialize AMU agent
amu_agent = AMUTrackingAgent()

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_antimicrobial_usage(
    request: AMUTrackingRequest
):
    """Analyze antimicrobial usage and detect anomalies"""
    try:
        context = {
            "prescription_data": request.dict(),
            "animal_id": request.animal_id,
            "farm_id": getattr(request, 'farm_id', '')
        }
        result = await amu_agent.execute("analyze_prescription", context)
        return result
    except Exception as e:
        logger.error(f"Error in AMU analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compliance", response_model=Dict[str, Any])
async def check_compliance(
    request: AMUTrackingRequest
):
    """Check antimicrobial usage compliance against guidelines"""
    try:
        context = {"usage_data": request.dict()}
        result = await amu_agent.execute("check_compliance", context)
        return result
    except Exception as e:
        logger.error(f"Error in compliance check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/guidelines")
async def get_usage_guidelines():
    """Get antimicrobial usage guidelines"""
    try:
        return {
            "guidelines": {
                "max_daily_dosage": amu_agent.guidelines.get("max_daily_dosage", {}),
                "max_treatment_duration": amu_agent.guidelines.get("max_treatment_duration", {}),
                "max_frequency": amu_agent.guidelines.get("max_frequency", {}),
                "critical_drugs": getattr(amu_agent, 'critical_drugs', [])
            }
        }
    except Exception as e:
        logger.error(f"Error getting guidelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def amu_health_check():
    """Health check for AMU tracking agent"""
    try:
        return await amu_agent.health_check()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))