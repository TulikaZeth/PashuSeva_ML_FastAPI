# MRL Compliance Agent API Routes
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from ..core.base import MRLComplianceRequest, MRLComplianceResponse
from ..agents.mrl_compliance_agent import MRLComplianceAgent
from ..services.database_service import db_service

router = APIRouter(prefix="/api/v1/mrl", tags=["MRL Compliance"])
logger = logging.getLogger(__name__)

# Initialize MRL agent
mrl_agent = MRLComplianceAgent()

def set_mrl_agent(agent):
    """Set the module-level MRL agent instance used by the API endpoints"""
    global mrl_agent
    mrl_agent = agent

def _generate_dummy_medications_for_mrl() -> List[Dict[str, Any]]:
    """
    Generate dummy medications for MRL analysis when no medications are found
    """
    return [
        {
            "normalized_name": "Penicillin G",
            "drug_name": "Penicillin G",
            "dosage": "20 mg/kg",
            "duration": "5 days",
            "route": "IM",
            "frequency": "Once daily",
            "dummy_data": True
        },
        {
            "normalized_name": "Oxytetracycline",
            "drug_name": "Oxytetracycline",
            "dosage": "10 mg/kg",
            "duration": "3 days",
            "route": "IV",
            "frequency": "Twice daily",
            "dummy_data": True
        },
        {
            "normalized_name": "Sulfadimidine",
            "drug_name": "Sulfadimidine",
            "dosage": "100 mg/kg",
            "duration": "7 days",
            "route": "Oral",
            "frequency": "Once daily",
            "dummy_data": True
        }
    ]

@router.post("/analyze/{tag_no}")
async def analyze_animal_mrl(
    tag_no: str,
    target_tissue: str = Query("muscle", description="Target tissue for analysis (muscle, milk, eggs, liver, kidney)"),
    days_since_treatment: int = Query(0, description="Days since last treatment (0 for current treatment)")
) -> Dict[str, Any]:
    """
    Comprehensive MRL analysis for an animal by tag number
    Fetches animal data from database and performs MRL compliance analysis
    """
    try:
        if not db_service or not db_service.is_connected:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Get animal data from database
        animal_data = await db_service.get_animal(tag_no)
        if not animal_data:
            raise HTTPException(status_code=404, detail=f"Animal with tag {tag_no} not found")
        
        # Extract animal information
        species = animal_data.get("species", "cattle")
        prescriptions = animal_data.get("prescriptions", [])
        
        if not prescriptions:
            return {
                "status": "success",
                "animal_id": tag_no,
                "species": species,
                "message": "No prescriptions found for this animal",
                "mrl_analysis": [],
                "overall_assessment": {
                    "compliant": True,
                    "total_medications": 0,
                    "high_risk_medications": 0,
                    "safety_status": "safe"
                }
            }
        
        # Perform MRL analysis on all prescriptions
        mrl_analyses = []
        logger.info(f"Processing {len(prescriptions)} prescriptions for MRL analysis")
        
        for prescription in prescriptions:
            logger.info(f"Processing prescription: {prescription.get('date', 'Unknown date')}")
            logger.info(f"Full prescription data: {prescription}")
            
            # Check if prescription is a string (raw text) instead of structured data
            if isinstance(prescription, str):
                logger.warning("Prescription is a string, generating dummy medications for MRL analysis")
                medications = _generate_dummy_medications_for_mrl()
            else:
                # Check for different possible medication field names
                medications = prescription.get("medications", [])
                if not medications:
                    # Try alternative field names
                    medications = prescription.get("medicines", [])
                    logger.info(f"Tried 'medicines' field, found {len(medications)} items")
                
                if not medications:
                    logger.warning("No medications found in prescription, generating dummy medications for MRL analysis")
                    medications = _generate_dummy_medications_for_mrl()
                
            logger.info(f"Found {len(medications)} medications in prescription")
            
            for i, medication in enumerate(medications):
                logger.info(f"Processing medication {i+1}: {medication}")
                logger.info(f"Medication keys: {list(medication.keys()) if isinstance(medication, dict) else 'Not a dict'}")
                
                # Try different possible drug name fields
                drug_name = medication.get("normalized_name", "")
                if not drug_name:
                    drug_name = medication.get("drug_name", "")
                if not drug_name:
                    drug_name = medication.get("name", "")
                if not drug_name:
                    drug_name = medication.get("medicine_name", "")
                
                logger.info(f"Extracted drug name: '{drug_name}'")
                if not drug_name:
                    logger.warning(f"No drug name found in medication: {medication}")
                    continue
                
                # Try different possible dosage and duration fields
                dosage_str = medication.get("dosage", "")
                if not dosage_str:
                    dosage_str = medication.get("dose", "")
                if not dosage_str:
                    dosage_str = medication.get("amount", "")
                
                duration_str = medication.get("duration", "")
                if not duration_str:
                    duration_str = medication.get("days", "")
                if not duration_str:
                    duration_str = medication.get("treatment_duration", "")
                
                logger.info(f"Raw dosage string: '{dosage_str}'")
                logger.info(f"Raw duration string: '{duration_str}'")
                
                # Parse dosage and duration with fallbacks
                dosage = mrl_agent._parse_dosage_value(dosage_str)
                duration = mrl_agent._parse_duration_value(duration_str)
                
                # If dosage is 0, try to use a default dosage for MRL analysis
                if dosage == 0:
                    logger.warning(f"Invalid dosage for {drug_name}: '{dosage_str}', using default")
                    dosage = 10.0  # Default dosage for MRL analysis
                
                # If duration is 0, use a default duration
                if duration == 0:
                    logger.warning(f"Invalid duration for {drug_name}: '{duration_str}', using default")
                    duration = 3  # Default duration
                
                logger.info(f"Final values - Drug: {drug_name}, Dosage: {dosage}, Duration: {duration}")
                
                # Predict residue levels
                predicted_residues = mrl_agent.predict_residue_levels(
                    drug_name, species, dosage, duration, days_since_treatment
                )
                
                # Check MRL compliance
                compliance_result = mrl_agent.check_mrl_compliance(drug_name, species, predicted_residues)
                compliance_result.animal_id = tag_no
                
                # Calculate optimal withdrawal period
                withdrawal_recommendation = mrl_agent.calculate_optimal_withdrawal_period(
                    drug_name, species, dosage, duration, target_tissue=target_tissue
                )
                
                # Generate safety alerts
                safety_alerts = mrl_agent.generate_safety_alerts(compliance_result)
                
                mrl_analyses.append({
                    "medication": medication.get("drug_name"),
                    "normalized_name": drug_name,
                    "prescription_date": prescription.get("date", ""),
                    "compliance_result": {
                        "compliance_status": compliance_result.compliance_status,
                        "predicted_residue_level": compliance_result.predicted_residue_level,
                        "mrl_limit": compliance_result.mrl_limit,
                        "safety_margin": compliance_result.safety_margin,
                        "risk_factors": compliance_result.risk_factors,
                        "confidence_score": compliance_result.confidence_score
                    },
                    "predicted_residues": predicted_residues,
                    "withdrawal_recommendation": withdrawal_recommendation,
                    "safety_alerts": safety_alerts,
                    "dummy_data": medication.get("dummy_data", False)
                })
        
        # Overall assessment
        overall_compliant = all(
            analysis["compliance_result"]["compliance_status"] == "compliant" 
            for analysis in mrl_analyses
        )
        
        high_risk_count = sum(
            1 for analysis in mrl_analyses 
            if analysis["compliance_result"]["compliance_status"] in ["violation", "at_risk"]
        )
        
        # Check if dummy data was used
        dummy_data_used = any(
            analysis.get("dummy_data", False) for analysis in mrl_analyses
        )
        
        return {
            "status": "success",
            "animal_id": tag_no,
            "species": species,
            "analysis_date": datetime.now().isoformat(),
            "target_tissue": target_tissue,
            "days_since_treatment": days_since_treatment,
            "animal_context": {
                "total_prescriptions": len(prescriptions),
                "total_medications_analyzed": len(mrl_analyses),
                "created_at": animal_data.get("createdAt"),
                "updated_at": animal_data.get("updatedAt")
            },
            "mrl_analysis": mrl_analyses,
            "overall_assessment": {
                "compliant": overall_compliant,
                "total_medications": len(mrl_analyses),
                "high_risk_medications": high_risk_count,
                "safety_status": "safe" if overall_compliant else "requires_attention",
                "dummy_data_used": dummy_data_used
            },
            "recommendations": mrl_agent._generate_general_mrl_recommendations(mrl_analyses)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing animal MRL: {e}")
        raise HTTPException(status_code=500, detail=f"MRL analysis failed: {str(e)}")

@router.post("/check-compliance")
async def check_specific_compliance(
    tag_no: str = Query(..., description="Animal tag number"),
    drug_name: str = Query(..., description="Drug name to check"),
    species: str = Query("cattle", description="Animal species"),
    dosage: float = Query(..., description="Drug dosage in mg/kg"),
    treatment_duration: int = Query(..., description="Treatment duration in days"),
    days_since_treatment: int = Query(0, description="Days since last treatment"),
    target_tissue: str = Query("muscle", description="Target tissue for analysis")
) -> Dict[str, Any]:
    """
    Check MRL compliance for a specific drug and animal
    """
    try:
        # Get animal data from database
        animal_data = None
        if db_service and db_service.is_connected:
            animal_data = await db_service.get_animal(tag_no)
        
        if not animal_data:
            # Use provided species if animal not found in database
            logger.warning(f"Animal {tag_no} not found in database, using provided species: {species}")
        else:
            species = animal_data.get("species", species)
        
        # Predict residue levels
        predicted_residues = mrl_agent.predict_residue_levels(
            drug_name, species, dosage, treatment_duration, days_since_treatment
        )
        
        # Check MRL compliance
        compliance_result = mrl_agent.check_mrl_compliance(drug_name, species, predicted_residues)
        compliance_result.animal_id = tag_no
        
        # Calculate optimal withdrawal period
        withdrawal_recommendation = mrl_agent.calculate_optimal_withdrawal_period(
            drug_name, species, dosage, treatment_duration, target_tissue=target_tissue
        )
        
        # Generate safety alerts
        safety_alerts = mrl_agent.generate_safety_alerts(compliance_result)
        
        return {
            "status": "success",
            "animal_id": tag_no,
            "species": species,
            "drug_name": drug_name,
            "analysis_date": datetime.now().isoformat(),
            "compliance_result": {
                "compliance_status": compliance_result.compliance_status,
                "predicted_residue_level": compliance_result.predicted_residue_level,
                "mrl_limit": compliance_result.mrl_limit,
                "safety_margin": compliance_result.safety_margin,
                "risk_factors": compliance_result.risk_factors,
                "confidence_score": compliance_result.confidence_score
            },
            "predicted_residues": predicted_residues,
            "withdrawal_recommendation": withdrawal_recommendation,
            "safety_alerts": safety_alerts,
            "animal_context": animal_data
        }
        
    except Exception as e:
        logger.error(f"Error checking MRL compliance: {e}")
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {str(e)}")

@router.get("/withdrawal-period/{tag_no}")
async def get_withdrawal_periods(
    tag_no: str,
    target_tissue: str = Query("muscle", description="Target tissue (muscle, milk, eggs)"),
    days_since_treatment: int = Query(0, description="Days since last treatment")
) -> Dict[str, Any]:
    """
    Get withdrawal period recommendations for an animal by tag number
    """
    try:
        if not db_service or not db_service.is_connected:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Get animal data from database
        animal_data = await db_service.get_animal(tag_no)
        if not animal_data:
            raise HTTPException(status_code=404, detail=f"Animal with tag {tag_no} not found")
        
        species = animal_data.get("species", "cattle")
        prescriptions = animal_data.get("prescriptions", [])
        
        withdrawal_recommendations = []
        
        # Analyze each prescription for withdrawal periods
        for prescription in prescriptions:
            if not prescription.get("medications"):
                continue
                
            for medication in prescription["medications"]:
                drug_name = medication.get("normalized_name", medication.get("drug_name", ""))
                if not drug_name:
                    continue
                
                dosage = mrl_agent._parse_dosage_value(medication.get("dosage", ""))
                duration = mrl_agent._parse_duration_value(medication.get("duration", ""))
                
                if dosage == 0:
                    continue
                
                # Calculate withdrawal period
                withdrawal_recommendation = mrl_agent.calculate_optimal_withdrawal_period(
                    drug_name, species, dosage, duration, target_tissue=target_tissue
                )
                
                withdrawal_recommendations.append({
                    "medication": medication.get("drug_name"),
                    "normalized_name": drug_name,
                    "prescription_date": prescription.get("date", ""),
                    "dosage": dosage,
                    "duration": duration,
                    "withdrawal_recommendation": withdrawal_recommendation,
                    "standard_withdrawal": mrl_agent.get_withdrawal_period(drug_name, species, target_tissue)
                })
        
        # Find the longest recommended withdrawal period
        max_withdrawal = 0
        if withdrawal_recommendations:
            max_withdrawal = max(
                rec["withdrawal_recommendation"]["recommended_days"] 
                for rec in withdrawal_recommendations
            )
        
        return {
            "status": "success",
            "animal_id": tag_no,
            "species": species,
            "target_tissue": target_tissue,
            "days_since_treatment": days_since_treatment,
            "withdrawal_recommendations": withdrawal_recommendations,
            "overall_recommendation": {
                "maximum_withdrawal_days": max_withdrawal,
                "recommended_wait_period": max(0, max_withdrawal - days_since_treatment),
                "safe_for_consumption": days_since_treatment >= max_withdrawal
            },
            "animal_context": {
                "total_prescriptions": len(prescriptions),
                "medications_analyzed": len(withdrawal_recommendations)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting withdrawal periods: {e}")
        raise HTTPException(status_code=500, detail=f"Withdrawal period calculation failed: {str(e)}")

@router.get("/standards/{species}")
async def get_mrl_standards(species: str):
    """Get MRL standards for specific species"""
    try:
        standards = mrl_agent.get_mrl_standards(species.lower())
        return {
            "status": "success",
            "species": species,
            "standards": standards,
            "tissue_types": ["muscle", "liver", "kidney", "milk", "eggs"],
            "supported_drugs": list(standards.keys()) if standards else []
        }
    except Exception as e:
        logger.error(f"Error getting MRL standards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-residue")
async def predict_residue_levels(
    tag_no: str = Query(..., description="Animal tag number"),
    drug_name: str = Query(..., description="Drug name"),
    days_since_treatment: int = Query(..., description="Days since last treatment"),
    dosage: float = Query(1.0, description="Drug dosage in mg/kg"),
    treatment_duration: int = Query(1, description="Treatment duration in days")
) -> Dict[str, Any]:
    """Predict residue levels using pharmacokinetic models"""
    try:
        # Get animal data from database
        animal_data = None
        species = "cattle"  # default
        
        if db_service and db_service.is_connected:
            animal_data = await db_service.get_animal(tag_no)
            if animal_data:
                species = animal_data.get("species", "cattle")
        
        # Predict residue levels
        predicted_residues = mrl_agent.predict_residue_levels(
            drug_name, species, dosage, treatment_duration, days_since_treatment
        )
        
        # Get MRL standards for comparison
        standards = mrl_agent.get_mrl_standards(species)
        drug_standards = standards.get(drug_name.lower(), {})
        
        return {
            "status": "success",
            "animal_id": tag_no,
            "species": species,
            "drug_name": drug_name,
            "days_since_treatment": days_since_treatment,
            "predicted_residues": predicted_residues,
            "mrl_standards": drug_standards,
            "compliance_check": {
                "muscle_compliant": predicted_residues.get("muscle", 0) <= drug_standards.get("muscle", {}).get("mrl_limit", 0.1),
                "liver_compliant": predicted_residues.get("liver", 0) <= drug_standards.get("liver", {}).get("mrl_limit", 0.3),
                "kidney_compliant": predicted_residues.get("kidney", 0) <= drug_standards.get("kidney", {}).get("mrl_limit", 0.6)
            },
            "animal_context": animal_data
        }
        
    except Exception as e:
        logger.error(f"Error predicting residue levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/{tag_no}")
async def debug_animal_data(tag_no: str) -> Dict[str, Any]:
    """
    Debug endpoint to inspect animal data structure
    """
    try:
        if not db_service or not db_service.is_connected:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Get animal data from database
        animal_data = await db_service.get_animal(tag_no)
        if not animal_data:
            raise HTTPException(status_code=404, detail=f"Animal with tag {tag_no} not found")
        
        # Extract and analyze prescription structure
        prescriptions = animal_data.get("prescriptions", [])
        prescription_analysis = []
        
        for i, prescription in enumerate(prescriptions):
            prescription_info = {
                "prescription_index": i,
                "date": prescription.get("date", "Unknown"),
                "veterinarian": prescription.get("veterinarian", "Unknown"),
                "keys": list(prescription.keys()),
                "medications_field_exists": "medications" in prescription,
                "medicines_field_exists": "medicines" in prescription,
                "medications_count": len(prescription.get("medications", [])),
                "medicines_count": len(prescription.get("medicines", [])),
                "raw_medications": prescription.get("medications", []),
                "raw_medicines": prescription.get("medicines", [])
            }
            prescription_analysis.append(prescription_info)
        
        return {
            "status": "success",
            "animal_id": tag_no,
            "species": animal_data.get("species", "Unknown"),
            "total_prescriptions": len(prescriptions),
            "prescription_analysis": prescription_analysis,
            "animal_keys": list(animal_data.keys()),
            "sample_prescription": prescriptions[0] if prescriptions else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error debugging animal data: {e}")
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

@router.get("/health")
async def mrl_health_check():
    """Health check for MRL compliance agent"""
    try:
        agent_info = await mrl_agent.get_agent_info()
        db_status = "connected" if db_service and db_service.is_connected else "disconnected"
        
        return {
            "status": "healthy",
            "agent": agent_info,
            "database": db_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))