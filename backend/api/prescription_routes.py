"""
Prescription Upload and Analysis Routes
Unified endpoint for comprehensive prescription analysis integrating OCR, NLP, AMU, MRL, and RAG
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import io
from PIL import Image
import json

from backend.core.base import PrescriptionAnalysisResponse, PrescriptionUploadRequest
from backend.agents.prescription_analyzer_agent import PrescriptionAnalyzerAgent
from backend.agents.amu_tracking_agent import AMUTrackingAgent
from backend.agents.mrl_compliance_agent import MRLComplianceAgent
from backend.services.rag_service import RAGService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prescription", tags=["prescription"])

# Global variables for agent services
prescription_analyzer = None
amu_agent = None
mrl_agent = None
rag_service = None

def set_prescription_analyzer(analyzer):
    global prescription_analyzer
    prescription_analyzer = analyzer

def set_amu_agent(agent):
    global amu_agent
    amu_agent = agent

def set_mrl_agent(agent):
    global mrl_agent
    mrl_agent = agent

def set_rag_service(service):
    global rag_service
    rag_service = service

@router.post("/upload")
async def upload_prescription(
    image: UploadFile = File(...),
    species: Optional[str] = Form("cattle"),
    additional_info: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Upload and analyze veterinary prescription image
    
    This endpoint provides comprehensive prescription analysis:
    1. OCR text extraction from prescription image
    2. NLP parsing to extract structured data
    3. AMU (Antimicrobial Usage) compliance analysis
    4. MRL (Maximum Residue Limit) compliance checking
    5. RAG-based animal record retrieval
    6. Unified analysis report
    """
    try:
        # Validate image file
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process image
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data))
        
        logger.info(f"Processing prescription image: {image.filename}")
        
        # Step 1: OCR and NLP Analysis
        prescription_analysis = await prescription_analyzer.analyze_prescription(pil_image)
        
        if prescription_analysis["status"] != "success":
            return {
                "status": "error",
                "message": "Failed to extract prescription data",
                "details": prescription_analysis
            }
        
        prescription_data = prescription_analysis["prescription_data"]
        prescription_data["species"] = species  # Add species info
        
        # Parse additional info if provided
        if additional_info:
            try:
                additional_data = json.loads(additional_info)
                prescription_data.update(additional_data)
            except json.JSONDecodeError:
                logger.warning("Could not parse additional_info as JSON")
        
        # Step 2: RAG Analysis (retrieve animal records)
        rag_results = None
        if prescription_data.get("animal_id"):
            try:
                from ..core.base import RAGRequest
                rag_request = RAGRequest(
                    tag_no=prescription_data['animal_id'],
                    question=f"What is the treatment history, medications and withdrawal information for animal {prescription_data['animal_id']}?"
                )
                rag_response = await rag_service.process(rag_request)
                rag_results = {"response": rag_response.answer if hasattr(rag_response, 'answer') else str(rag_response)}
                logger.info(f"Retrieved RAG data for animal {prescription_data['animal_id']}")
            except Exception as e:
                logger.warning(f"RAG query failed: {e}")
                rag_results = {"response": "No historical data available"}
        
        # Step 3: AMU Analysis
        amu_analysis = None
        if prescription_data.get("medications"):
            try:
                if amu_agent:
                    amu_analysis = await amu_agent.analyze_prescription_usage(prescription_data)
                    logger.info("Completed AMU analysis")
                else:
                    logger.warning("AMU agent not initialized")
                    amu_analysis = {"status": "unavailable", "message": "AMU agent not initialized"}
            except Exception as e:
                logger.error(f"AMU analysis failed: {e}")
                amu_analysis = {"status": "error", "message": str(e)}
        
        # Step 4: MRL Analysis
        mrl_analysis = None
        if prescription_data.get("medications"):
            try:
                if mrl_agent:
                    mrl_analysis = await mrl_agent.analyze_prescription_mrl(prescription_data)
                    logger.info("Completed MRL analysis")
                else:
                    logger.warning("MRL agent not initialized")
                    mrl_analysis = {"status": "unavailable", "message": "MRL agent not initialized"}
            except Exception as e:
                logger.error(f"MRL analysis failed: {e}")
                mrl_analysis = {"status": "error", "message": str(e)}
        
        # Step 5: Generate Unified Analysis Report
        unified_report = generate_unified_report(
            prescription_data, rag_results, amu_analysis, mrl_analysis
        )
        
        return {
            "status": "success",
            "message": "Prescription analysis completed successfully",
            "prescription_data": prescription_data,
            "analysis_results": {
                "ocr_confidence": prescription_analysis.get("ocr_confidence", 0.0),
                "raw_text": prescription_analysis.get("raw_text", ""),
                "rag_analysis": rag_results,
                "amu_analysis": amu_analysis,
                "mrl_analysis": mrl_analysis
            },
            "unified_report": unified_report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing prescription upload: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

def generate_unified_report(
    prescription_data: Dict[str, Any],
    rag_results: Optional[Dict[str, Any]],
    amu_analysis: Optional[Dict[str, Any]],
    mrl_analysis: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate unified analysis report combining all analyses
    """
    try:
        report = {
            "animal_id": prescription_data.get("animal_id", "Unknown"),
            "species": prescription_data.get("species", "Unknown"),
            "analysis_timestamp": prescription_data.get("date", "Unknown"),
            "medications_count": len(prescription_data.get("medications", [])),
            "overall_status": "unknown",
            "risk_level": "unknown",
            "compliance_status": "unknown",
            "key_findings": [],
            "critical_alerts": [],
            "recommendations": [],
            "withdrawal_periods": {},
            "summary": ""
        }
        
        critical_alerts = []
        recommendations = []
        withdrawal_periods = {}
        
        # Process AMU Analysis Results
        if amu_analysis and amu_analysis.get("status") == "success":
            amu_overall = amu_analysis.get("overall_assessment", {})
            
            if not amu_overall.get("compliant", True):
                critical_alerts.append("AMU guideline violations detected")
                report["risk_level"] = "high"
            
            if amu_overall.get("total_anomalies", 0) > 0:
                critical_alerts.append(f"AMU anomalies detected: {amu_overall.get('total_anomalies')}")
            
            if amu_overall.get("critical_drugs_used", 0) > 0:
                critical_alerts.append("Critical antimicrobials prescribed - special monitoring required")
            
            recommendations.extend(amu_analysis.get("recommendations", []))
        
        # Process MRL Analysis Results
        if mrl_analysis and mrl_analysis.get("status") == "success":
            mrl_overall = mrl_analysis.get("overall_assessment", {})
            
            if not mrl_overall.get("compliant", True):
                critical_alerts.append("MRL compliance issues detected")
                report["risk_level"] = "high"
            
            if mrl_overall.get("high_risk_medications", 0) > 0:
                critical_alerts.append(f"High-risk medications for MRL: {mrl_overall.get('high_risk_medications')}")
            
            # Extract withdrawal periods
            for analysis in mrl_analysis.get("mrl_analyses", []):
                med_name = analysis.get("medication", "Unknown")
                withdrawal_rec = analysis.get("withdrawal_recommendation", {})
                if withdrawal_rec:
                    withdrawal_periods[med_name] = withdrawal_rec.get("recommended_days", "Unknown")
            
            recommendations.extend(mrl_analysis.get("general_recommendations", []))
        
        # Process RAG Results
        if rag_results and rag_results.get("response"):
            report["animal_history"] = "Available"
            if "previous treatment" in rag_results["response"].lower():
                recommendations.append("Review animal treatment history for potential interactions")
        else:
            report["animal_history"] = "Not available"
            recommendations.append("Establish baseline animal health records")
        
        # Determine Overall Status
        if critical_alerts:
            report["overall_status"] = "requires_attention"
            report["compliance_status"] = "non_compliant"
        else:
            report["overall_status"] = "compliant"
            report["compliance_status"] = "compliant"
        
        # Set risk level if not already set
        if report["risk_level"] == "unknown":
            if critical_alerts:
                report["risk_level"] = "medium"
            else:
                report["risk_level"] = "low"
        
        # Generate Key Findings
        key_findings = []
        if prescription_data.get("medications"):
            key_findings.append(f"Prescribed {len(prescription_data['medications'])} medication(s)")
        
        if amu_analysis and amu_analysis.get("status") == "success":
            amu_overall = amu_analysis.get("overall_assessment", {})
            key_findings.append(f"AMU Compliance: {'Yes' if amu_overall.get('compliant') else 'No'}")
        
        if mrl_analysis and mrl_analysis.get("status") == "success":
            mrl_overall = mrl_analysis.get("overall_assessment", {})
            key_findings.append(f"MRL Compliance: {'Yes' if mrl_overall.get('compliant') else 'No'}")
        
        # Generate Summary
        summary_parts = []
        
        if report["compliance_status"] == "compliant":
            summary_parts.append("Prescription appears compliant with veterinary guidelines.")
        else:
            summary_parts.append("Prescription has compliance issues requiring attention.")
        
        if withdrawal_periods:
            max_withdrawal = max([
                int(period) for period in withdrawal_periods.values() 
                if isinstance(period, (int, str)) and str(period).isdigit()
            ], default=0)
            if max_withdrawal > 0:
                summary_parts.append(f"Maximum withdrawal period: {max_withdrawal} days.")
        
        if critical_alerts:
            summary_parts.append(f"Critical alerts: {len(critical_alerts)} items require immediate attention.")
        
        # Populate final report
        report.update({
            "key_findings": key_findings,
            "critical_alerts": critical_alerts,
            "recommendations": list(set(recommendations)),  # Remove duplicates
            "withdrawal_periods": withdrawal_periods,
            "summary": " ".join(summary_parts) if summary_parts else "Analysis completed."
        })
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating unified report: {e}")
        return {
            "error": "Failed to generate unified report",
            "details": str(e)
        }

@router.get("/analyze/{animal_id}")
async def get_animal_prescription_history(animal_id: str) -> Dict[str, Any]:
    """
    Get comprehensive prescription and treatment history for an animal
    """
    try:
        # Query RAG for animal history
        from ..core.base import RAGRequest
        rag_request = RAGRequest(
            tag_no=animal_id,
            question=f"What are the prescriptions, treatments, medications and history for animal {animal_id}?"
        )
        rag_response = await rag_service.process(rag_request)
        rag_results = rag_response.answer if hasattr(rag_response, 'answer') else str(rag_response)
        
        # Get AMU usage summary
        try:
            amu_summary = {"status": "AMU service not available", "usage_data": []}
            # amu_summary = await amu_agent.get_usage_summary(animal_id)
        except Exception as e:
            logger.warning(f"AMU summary failed: {e}")
            amu_summary = {"status": "AMU service error", "error": str(e)}
        
        # Get agent information
        try:
            amu_info = {"agent_name": "AMU Tracking Agent", "status": "available"}
            mrl_info = {"agent_name": "MRL Compliance Agent", "status": "available"}
            # amu_info = await amu_agent.get_agent_info()
            # mrl_info = await mrl_agent.get_agent_info()
        except Exception as e:
            logger.warning(f"Agent info failed: {e}")
            amu_info = {"agent_name": "AMU Tracking Agent", "status": "error"}
            mrl_info = {"agent_name": "MRL Compliance Agent", "status": "error"}
        
        return {
            "status": "success",
            "animal_id": animal_id,
            "historical_data": rag_results if isinstance(rag_results, str) else rag_results.get("response", "No historical data found"),
            "amu_summary": amu_summary,
            "agent_capabilities": {
                "amu_agent": amu_info,
                "mrl_agent": mrl_info
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving animal history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@router.get("/agents/status")
async def get_agents_status() -> Dict[str, Any]:
    """
    Get status and capabilities of all prescription analysis agents
    """
    try:
        status = {}
        
        if prescription_analyzer:
            status["prescription_analyzer"] = await prescription_analyzer.get_analysis_summary()
        else:
            status["prescription_analyzer"] = {"status": "not_initialized", "description": "Prescription analyzer not available"}
            
        if amu_agent:
            status["amu_agent"] = await amu_agent.get_agent_info()
        else:
            status["amu_agent"] = {"status": "not_initialized", "description": "AMU tracking agent not available"}
            
        if mrl_agent:
            status["mrl_agent"] = await mrl_agent.get_agent_info()
        else:
            status["mrl_agent"] = {"status": "not_initialized", "description": "MRL compliance agent not available"}
            
        if rag_service:
            status["rag_service"] = {"status": "active", "description": "Knowledge retrieval service"}
        else:
            status["rag_service"] = {"status": "not_initialized", "description": "RAG service not available"}
            
        return status
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
    """Validate prescription format and completeness"""
    try:
        validation_result = agent.validate_prescription_format(prescription_data)
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")