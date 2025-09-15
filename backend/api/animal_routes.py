# Unified Animal-Based API Routes
# All functionality accessible by animal tag number
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..services.database_service import db_service
from ..services.rag_service import RAGService
from ..services.chat_service import ChatService
from ..agents.amu_tracking_agent import AMUTrackingAgent
from ..agents.mrl_compliance_agent import MRLComplianceAgent
from ..agents.risk_prediction_agent import RiskPredictionAgent
from ..core.base import RAGRequest

router = APIRouter(prefix="/animal", tags=["Animal-Centric API"])
logger = logging.getLogger(__name__)

# Global services - will be injected from main.py
rag_service = None
chat_service = None
amu_agent = None
mrl_agent = None
risk_agent = None

def set_services(rag_svc, chat_svc, amu_agt, mrl_agt, risk_agt):
    """Set all service instances"""
    global rag_service, chat_service, amu_agent, mrl_agent, risk_agent
    rag_service = rag_svc
    chat_service = chat_svc
    amu_agent = amu_agt
    mrl_agent = mrl_agt
    risk_agent = risk_agt

@router.get("/{tag_no}")
async def get_animal_overview(tag_no: str):
    """Get complete overview of an animal by tag number"""
    try:
        # Get basic animal data
        animal_data = await db_service.get_animal(tag_no)
        if not animal_data:
            raise HTTPException(status_code=404, detail=f"Animal {tag_no} not found")
        
        return {
            "tagNo": tag_no,
            "basicInfo": {
                "breed": animal_data.get("breed"),
                "gender": animal_data.get("gender"),
                "farmId": animal_data.get("farmId"),
                "dateOfAdmission": animal_data.get("dateOfAdmission"),
                "complianceStatus": animal_data.get("complianceStatus")
            },
            "healthStatus": {
                "vaccination": animal_data.get("vaccination", False),
                "insurance": animal_data.get("insurance", False),
                "lastVisit": animal_data.get("doctorVisits", [])[-1] if animal_data.get("doctorVisits") else None
            },
            "recordCounts": {
                "prescriptions": len(animal_data.get("prescriptions", [])),
                "treatments": len(animal_data.get("treatments", [])),
                "doctorVisits": len(animal_data.get("doctorVisits", [])),
                "historyEntries": len(animal_data.get("history", []))
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting animal overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tag_no}/rag")
async def get_animal_rag_analysis(tag_no: str, question: Optional[str] = None):
    """Get RAG analysis for an animal"""
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG service not available")
        
        # Default question if none provided
        if not question:
            question = f"What is the complete health profile, treatment history, and current status of animal {tag_no}?"
        
        # Create RAG request
        rag_request = RAGRequest(tag_no=tag_no, question=question)
        rag_response = await rag_service.process(rag_request)
        
        return {
            "tagNo": tag_no,
            "question": question,
            "analysis": rag_response.answer if hasattr(rag_response, 'answer') else str(rag_response),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in RAG analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tag_no}/amu")
async def get_animal_amu_analysis(tag_no: str):
    """Get AMU (Antimicrobial Use) analysis for an animal"""
    try:
        animal_data = await db_service.get_animal(tag_no)
        if not animal_data:
            raise HTTPException(status_code=404, detail=f"Animal {tag_no} not found")

        prescriptions = animal_data.get("prescriptions", [])
        treatments = animal_data.get("treatments", [])

        if not amu_agent:
            antimicrobials_used = []
            for prescription in prescriptions:
                for medicine in prescription.get("medicines", []):
                    antimicrobials_used.append({
                        "drug": medicine.get("name"),
                        "dosage": medicine.get("dosage"),
                        "duration": medicine.get("duration"),
                        "frequency": medicine.get("frequency"),
                        "date": prescription.get("date")
                    })

            return {
                "tagNo": tag_no,
                "amuAnalysis": {
                    "totalPrescriptions": len(prescriptions),
                    "totalTreatments": len(treatments),
                    "antimicrobialsUsed": antimicrobials_used,
                    "riskLevel": (
                        "low" if len(antimicrobials_used) <= 3
                        else "medium" if len(antimicrobials_used) <= 6
                        else "high"
                    ),
                    "recommendations": [
                        "Monitor withdrawal periods",
                        "Follow veterinary prescription guidelines",
                        "Maintain treatment records"
                    ]
                },
                "timestamp": datetime.now().isoformat()
            }

        # Otherwise, prepare structured prescription data for the agent
        prescription_data = {
            "animal_id": tag_no,
            "medications": [],
            "date": datetime.now().isoformat(),
            "veterinarian": "system"
        }

        for prescription in prescriptions:
            for medicine in prescription.get("medicines", []):
                prescription_data["medications"].append({
                    "drug_name": medicine.get("name", ""),
                    "normalized_name": medicine.get("name", "").lower(),
                    "dosage": medicine.get("dosage", ""),
                    "frequency": medicine.get("frequency", ""),
                    "duration": medicine.get("duration", ""),
                    "route": medicine.get("route", "oral")
                })

        # Pass to AMU agent
        result = await amu_agent.analyze_prescription_usage(prescription_data)

        return {
            "tagNo": tag_no,
            "amuAnalysis": result,
            "context": {
                "prescriptions": prescriptions,
                "treatments": treatments,
                "animalInfo": {
                    "breed": animal_data.get("breed"),
                    "gender": animal_data.get("gender"),
                    "farmId": animal_data.get("farmId"),
                    "complianceStatus": animal_data.get("complianceStatus")
                },
                "prescription_summary": {
                    "total_prescriptions": len(prescriptions),
                    "total_treatments": len(treatments),
                    "medications_analyzed": len(prescription_data["medications"])
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AMU analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tag_no}/mrl")
async def get_animal_mrl_analysis(tag_no: str):
    """Get MRL (Maximum Residue Limit) analysis for an animal"""
    try:
        # Get animal data
        animal_data = await db_service.get_animal(tag_no)
        if not animal_data:
            raise HTTPException(status_code=404, detail=f"Animal {tag_no} not found")
        
        # Extract relevant data
        prescriptions = animal_data.get("prescriptions", [])
        breed = animal_data.get("breed", "cattle")
        
        # Get last treatment date
        last_treatment_date = None
        if prescriptions:
            last_prescription = max(prescriptions, key=lambda x: x.get("date", ""))
            last_treatment_date = last_prescription.get("date")
        
        if not mrl_agent:
            # Provide manual MRL analysis
            withdrawal_info = []
            for prescription in prescriptions:
                for medicine in prescription.get("medicines", []):
                    withdrawal_info.append({
                        "drug": medicine.get("name"),
                        "withdrawalPeriod": "7 days",  # Default
                        "safeDate": "Calculate based on last treatment",
                        "riskLevel": "low"
                    })
            
            return {
                "tagNo": tag_no,
                "mrlAnalysis": {
                    "species": breed,
                    "lastTreatmentDate": last_treatment_date,
                    "withdrawalInfo": withdrawal_info,
                    "overallCompliance": "compliant" if withdrawal_info else "no_treatments",
                    "recommendations": [
                        "Observe withdrawal periods before slaughter",
                        "Maintain accurate treatment records",
                        "Consult veterinarian for specific withdrawal times"
                    ]
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # Use MRL agent if available
        context = {
            "animal_id": tag_no,
            "species": breed,
            "prescriptions": prescriptions,
            "last_treatment_date": last_treatment_date
        }
        result = await mrl_agent.execute("analyze_compliance", context)
        return {
            "tagNo": tag_no,
            "mrlAnalysis": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in MRL analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tag_no}/amr")
async def get_animal_amr_analysis(tag_no: str):
    """Get AMR (Antimicrobial Resistance) risk analysis for an animal"""
    try:
        # Get animal data
        animal_data = await db_service.get_animal(tag_no)
        if not animal_data:
            raise HTTPException(status_code=404, detail=f"Animal {tag_no} not found")
        
        # Extract data for risk analysis
        prescriptions = animal_data.get("prescriptions", [])
        treatments = animal_data.get("treatments", [])
        history = animal_data.get("history", [])
        
        if not risk_agent:
            # Manual AMR risk analysis
            antimicrobial_count = 0
            unique_drugs = set()
            
            for prescription in prescriptions:
                for medicine in prescription.get("medicines", []):
                    drug_name = medicine.get("name", "").lower()
                    if any(term in drug_name for term in ["cillin", "mycin", "cycline", "sulfa"]):
                        antimicrobial_count += 1
                        unique_drugs.add(medicine.get("name"))
            
            risk_score = min(antimicrobial_count * 0.15, 1.0)
            risk_level = "low" if risk_score < 0.3 else "medium" if risk_score < 0.7 else "high"
            
            return {
                "tagNo": tag_no,
                "amrAnalysis": {
                    "riskScore": risk_score,
                    "riskLevel": risk_level,
                    "antimicrobialExposure": {
                        "totalTreatments": antimicrobial_count,
                        "uniqueDrugs": len(unique_drugs),
                        "drugsUsed": list(unique_drugs)
                    },
                    "riskFactors": [
                        f"Multiple antimicrobial treatments ({antimicrobial_count})" if antimicrobial_count > 3 else None,
                        f"Various drug classes used ({len(unique_drugs)})" if len(unique_drugs) > 2 else None
                    ],
                    "recommendations": [
                        "Use antimicrobials judiciously",
                        "Complete full treatment courses",
                        "Consider sensitivity testing",
                        "Monitor for treatment failures"
                    ]
                },
                "timestamp": datetime.now().isoformat()
            }
        
        # Use risk agent if available
        context = {
            "animal_id": tag_no,
            "treatment_history": prescriptions + treatments,
            "animal_characteristics": {
                "breed": animal_data.get("breed"),
                "gender": animal_data.get("gender"),
                "age": "unknown"  # Calculate from admission date if needed
            }
        }
        result = await risk_agent.execute("predict_amr_risk", context)
        return {
            "tagNo": tag_no,
            "amrAnalysis": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AMR analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{tag_no}/chat")
async def chat_about_animal(tag_no: str, question: str):
    """Chat about a specific animal using natural language"""
    try:
        # Get animal data for context
        animal_data = await db_service.get_animal(tag_no)
        if not animal_data:
            raise HTTPException(status_code=404, detail=f"Animal {tag_no} not found")
        
        # Prepare context for chat
        context_summary = f"""
        Animal {tag_no} Information:
        - Breed: {animal_data.get('breed')}
        - Gender: {animal_data.get('gender')}
        - Farm: {animal_data.get('farmId')}
        - Prescriptions: {len(animal_data.get('prescriptions', []))}
        - Treatments: {len(animal_data.get('treatments', []))}
        - Doctor Visits: {len(animal_data.get('doctorVisits', []))}
        """
        
        if not chat_service:
            # Provide basic response if chat service not available
            return {
                "tagNo": tag_no,
                "question": question,
                "response": f"Based on available data for animal {tag_no}: {context_summary}. Please ask more specific questions about treatments, prescriptions, or health status.",
                "timestamp": datetime.now().isoformat()
            }
        
        # Use chat service
        enhanced_question = f"Question about animal {tag_no}: {question}\n\nContext: {context_summary}"
        from ..core.base import ChatRequest
        chat_request = ChatRequest(message=enhanced_question)
        chat_response = await chat_service.process(chat_request)
        
        return {
            "tagNo": tag_no,
            "question": question,
            "response": chat_response.response if hasattr(chat_response, 'response') else str(chat_response),
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tag_no}/comprehensive")
async def get_comprehensive_analysis(tag_no: str):
    """Get comprehensive analysis combining all services for an animal"""
    try:
        # Get basic animal data
        animal_data = await db_service.get_animal(tag_no)
        if not animal_data:
            raise HTTPException(status_code=404, detail=f"Animal {tag_no} not found")
        
        # Run all analyses
        results = {
            "tagNo": tag_no,
            "timestamp": datetime.now().isoformat(),
            "basicInfo": {
                "breed": animal_data.get("breed"),
                "gender": animal_data.get("gender"),
                "farmId": animal_data.get("farmId"),
                "complianceStatus": animal_data.get("complianceStatus")
            }
        }
        
        # Try to get each analysis, continue if one fails
        try:
            rag_result = await get_animal_rag_analysis(tag_no)
            results["ragAnalysis"] = rag_result["analysis"]
        except Exception as e:
            results["ragAnalysis"] = f"RAG analysis unavailable: {str(e)}"
        
        try:
            amu_result = await get_animal_amu_analysis(tag_no)
            results["amuAnalysis"] = amu_result["amuAnalysis"]
        except Exception as e:
            results["amuAnalysis"] = f"AMU analysis unavailable: {str(e)}"
        
        try:
            mrl_result = await get_animal_mrl_analysis(tag_no)
            results["mrlAnalysis"] = mrl_result["mrlAnalysis"]
        except Exception as e:
            results["mrlAnalysis"] = f"MRL analysis unavailable: {str(e)}"
        
        try:
            amr_result = await get_animal_amr_analysis(tag_no)
            results["amrAnalysis"] = amr_result["amrAnalysis"]
        except Exception as e:
            results["amrAnalysis"] = f"AMR analysis unavailable: {str(e)}"
        
        return results
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))