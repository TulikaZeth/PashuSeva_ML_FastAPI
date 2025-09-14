# MRL Compliance Agent API Routes
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from ..core.base import MRLComplianceRequest, MRLComplianceResponse
from ..agents.mrl_compliance_agent import MRLComplianceAgent

router = APIRouter(prefix="/api/v1/mrl", tags=["MRL Compliance"])
logger = logging.getLogger(__name__)

# Initialize MRL agent
mrl_agent = MRLComplianceAgent()

@router.post("/check", response_model=Dict[str, Any])
async def check_mrl_compliance(
    request: MRLComplianceRequest
):
    """Check MRL compliance and withdrawal periods"""
    try:
        context = {
            "animal_id": request.animal_id,
            "species": request.species,
            "drug_name": request.drug_name,
            "last_treatment_date": request.last_treatment_date,
            "slaughter_date": request.slaughter_date
        }
        result = await mrl_agent.execute("check_compliance", context)
        return result
    except Exception as e:
        logger.error(f"Error in MRL compliance check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-withdrawal", response_model=Dict[str, Any])
async def calculate_withdrawal_period(
    species: str,
    drug: str,
    dosage: float,
    treatment_duration: int
):
    """Calculate optimal withdrawal period"""
    try:
        context = {
            "species": species,
            "drug": drug,
            "dosage": dosage,
            "treatment_duration": treatment_duration
        }
        result = await mrl_agent.execute("calculate_withdrawal", context)
        return result
    except Exception as e:
        logger.error(f"Error in withdrawal calculation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/standards/{species}")
async def get_mrl_standards(species: str):
    """Get MRL standards for specific species"""
    try:
        standards = mrl_agent.mrl_standards.get(species.lower(), {})
        return {"species": species, "standards": standards}
    except Exception as e:
        logger.error(f"Error getting MRL standards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-residue")
async def predict_residue_levels(
    species: str,
    drug: str,
    days_since_treatment: int,
    base_concentration: float = 1.0
):
    """Predict residue levels using pharmacokinetic models"""
    try:
        context = {
            "species": species,
            "drug": drug,
            "days_since_treatment": days_since_treatment,
            "base_concentration": base_concentration
        }
        result = await mrl_agent.execute("predict_residue", context)
        return result
    except Exception as e:
        logger.error(f"Error predicting residue levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def mrl_health_check():
    """Health check for MRL compliance agent"""
    try:
        return await mrl_agent.health_check()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))