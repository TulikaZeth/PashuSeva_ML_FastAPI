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
from backend.services.database_service import db_service
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
    additional_info: Optional[str] = Form(None),
    tag_no: Optional[str] = Form(None)
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

        # Optionally refine extracted text using Gemini via RAGService, then re-parse
        prescription_data = prescription_analysis["prescription_data"]
        raw_text = prescription_analysis.get("raw_text", "")
        try:
            if rag_service and raw_text:
                refined_text = await rag_service.refine_text_with_gemini(raw_text)
                # re-parse refined text to get better structured fields
                try:
                    parsed = prescription_analyzer.parse_prescription(refined_text)
                    # parsed may be a dataclass; convert to dict-like
                    if hasattr(parsed, '__dict__'):
                        prescription_data = parsed.__dict__
                    else:
                        prescription_data = parsed
                    prescription_analysis['raw_text'] = refined_text
                except Exception:
                    # fallback to original parsed data
                    pass
        except Exception as e:
            logger.debug(f"Text refinement skipped or failed: {e}")

        prescription_data["species"] = species  # Add species info
        
        # Parse additional info if provided
        if additional_info:
            try:
                additional_data = json.loads(additional_info)
                prescription_data.update(additional_data)
            except json.JSONDecodeError:
                logger.warning("Could not parse additional_info as JSON")
        
        # Use tag_no as the primary animal identifier
        provided_tag = tag_no

        # If we still don't have a tag number, ask the client to provide it
        if not provided_tag:
            return JSONResponse(status_code=400, content={
                "status": "need_tag_no",
                "message": "Tag number (tag_no) is required to associate this prescription with an animal. Please resubmit with a tag_no.",
                "extracted_text": prescription_analysis.get("raw_text", "")
            })

        # Update prescription_data to use tag_no as animal_id
        prescription_data["animal_id"] = provided_tag

        # Step 2: RAG Analysis (retrieve animal records)
        rag_results = None
        if provided_tag:
            try:
                from ..core.base import RAGRequest
                rag_request = RAGRequest(
                    tag_no=provided_tag,
                    question=f"What is the treatment history, medications and withdrawal information for animal {provided_tag}?"
                )
                rag_response = await rag_service.process(rag_request)
                rag_results = {"response": rag_response.answer if hasattr(rag_response, 'answer') else str(rag_response)}
                logger.info(f"Retrieved RAG data for animal {provided_tag}")
            except Exception as e:
                logger.warning(f"RAG query failed: {e}")
                rag_results = {"response": "No historical data available"}

        # Step 2.5: Retrieve comprehensive animal data from database
        animal_context = None
        try:
            if db_service and db_service.is_connected:
                existing = await db_service.get_animal(provided_tag)
                if existing:
                    # Animal exists - retrieve full context
                    animal_context = {
                        "animal_id": existing.get("tagNo", provided_tag),
                        "species": existing.get("species", species),
                        "summary": existing.get("summary", ""),
                        "existing_prescriptions": existing.get("prescriptions", []),
                        "treatments": existing.get("treatments", []),
                        "history": existing.get("history", []),
                        "created_at": existing.get("createdAt", ""),
                        "updated_at": existing.get("updatedAt", ""),
                        "total_prescriptions": len(existing.get("prescriptions", [])),
                        "total_treatments": len(existing.get("treatments", [])),
                        "data_source": "database"
                    }
                    
                    # Add current prescription to existing prescriptions
                    updated_prescriptions = existing.get("prescriptions", []) + [prescription_data]
                    
                    # Update the animal record with new prescription
                    update_data = {
                        "prescriptions": updated_prescriptions,
                        "updatedAt": __import__('datetime').datetime.now().isoformat()
                    }
                    await db_service.update_animal(provided_tag, update_data)
                    logger.info(f"Updated animal record for tag {provided_tag} with new prescription")
                    
                else:
                    # Animal doesn't exist - create new record
                    animal_doc = {
                        "tagNo": provided_tag,
                        "species": species,
                        "summary": "Created from prescription upload",
                        "prescriptions": [prescription_data],
                        "treatments": [],
                        "history": [],
                        "createdAt": __import__('datetime').datetime.now().isoformat(),
                        "updatedAt": __import__('datetime').datetime.now().isoformat()
                    }
                    inserted = await db_service.insert_animal(animal_doc)
                    if inserted:
                        animal_context = {
                            "animal_id": provided_tag,
                            "species": species,
                            "summary": "Created from prescription upload",
                            "existing_prescriptions": [],
                            "treatments": [],
                            "history": [],
                            "created_at": animal_doc["createdAt"],
                            "updated_at": animal_doc["updatedAt"],
                            "total_prescriptions": 1,
                            "total_treatments": 0,
                            "data_source": "new_record"
                        }
                        logger.info(f"Created new animal record for tag {provided_tag}")
        except Exception as e:
            logger.warning(f"Failed to retrieve/update animal data: {e}")
            animal_context = {
                "animal_id": provided_tag,
                "species": species,
                "error": f"Database error: {str(e)}",
                "data_source": "error"
            }
        
        # Step 3: AMU Analysis
        # Before running AMU/MRL, try a single Gemini pass to extract only medicines
        try:
            prescription_data = await _extract_medicines_with_gemini(prescription_data, rag_service, prescription_analysis.get("raw_text", ""))
        except Exception as e:
            logger.debug(f"Medicines extraction pass failed: {e}")

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
            prescription_data, rag_results, amu_analysis, mrl_analysis, animal_context
        )
        
        return {
            "status": "success",
            "message": "Prescription analysis completed successfully",
            "prescription_data": prescription_data,
            "animal_context": animal_context,
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
    mrl_analysis: Optional[Dict[str, Any]],
    animal_context: Optional[Dict[str, Any]] = None
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
            "summary": "",
            "animal_context": animal_context or {}
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
        
        # Animal context findings
        if animal_context:
            if animal_context.get("data_source") == "database":
                key_findings.append(f"Animal {animal_context.get('animal_id')} found in database with {animal_context.get('total_prescriptions', 0)} previous prescriptions")
                if animal_context.get("total_treatments", 0) > 0:
                    key_findings.append(f"Animal has {animal_context.get('total_treatments', 0)} treatment records")
            elif animal_context.get("data_source") == "new_record":
                key_findings.append(f"New animal record created for {animal_context.get('animal_id')}")
            elif animal_context.get("data_source") == "error":
                key_findings.append(f"Database error: {animal_context.get('error', 'Unknown error')}")
        
        if prescription_data.get("medications"):
            med_count = len(prescription_data['medications'])
            dummy_used = prescription_data.get("dummy_data_used", False)
            if dummy_used:
                key_findings.append(f"Using {med_count} dummy medication(s) for testing (no real medications found)")
            else:
                key_findings.append(f"Prescribed {med_count} medication(s)")
        
        if amu_analysis and amu_analysis.get("status") == "success":
            amu_overall = amu_analysis.get("overall_assessment", {})
            key_findings.append(f"AMU Compliance: {'Yes' if amu_overall.get('compliant') else 'No'}")
            if amu_overall.get("dummy_data_used"):
                key_findings.append("Note: Analysis based on dummy data for testing")
        
        if mrl_analysis and mrl_analysis.get("status") == "success":
            mrl_overall = mrl_analysis.get("overall_assessment", {})
            key_findings.append(f"MRL Compliance: {'Yes' if mrl_overall.get('compliant') else 'No'}")
        
        # Generate Summary
        summary_parts = []
        
        # Check if dummy data was used
        dummy_data_used = prescription_data.get("dummy_data_used", False)
        if dummy_data_used:
            summary_parts.append("Analysis performed using dummy medication data for testing purposes.")
        
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


async def _extract_medicines_with_gemini(prescription_data: Dict[str, Any], rag_service: Optional[RAGService], raw_text: str) -> Dict[str, Any]:
    """Call Gemini once (via RAGService) to detect and structure medicines from the prescription.

    Returns potentially-updated prescription_data where 'medications' contains only the medicines detected by Gemini.
    This function is defensive: if Gemini/refinement fails or returns nothing usable, the original prescription_data is returned unchanged.
    """
    try:
        if not rag_service or not raw_text:
            return prescription_data

        # Use a targeted instruction to Gemini to return a JSON array of medicines only
        instruction = (
            "Extract and return ONLY the list of prescribed medicines from the following prescription text. "
            "Return a JSON array of objects with keys: name, dose (if available), frequency (if available), duration (if available). "
            "If no medicines are found, return an empty JSON array. Do not include any other text."
        )

        prompt_text = f"Instruction: {instruction}\n\nText:\n{raw_text}\n\nMedicines JSON:" 
        response = await rag_service.refine_text_with_gemini(prompt_text)

        # Try to parse JSON from the response
        meds = None
        try:
            # If the assistant returned just the JSON, load it; otherwise try to extract the first JSON substring
            resp = response.strip()
            if resp.startswith('{') or resp.startswith('['):
                meds = json.loads(resp)
            else:
                # attempt to find the first JSON array in the text
                start = resp.find('[')
                end = resp.rfind(']')
                if start != -1 and end != -1 and end > start:
                    meds = json.loads(resp[start:end+1])
        except Exception:
            meds = None

        if isinstance(meds, list):
            # Update prescription_data medications only if we got a list
            prescription_data['medications'] = meds

    except Exception as e:
        logger.debug(f"Medicine extraction with Gemini failed or returned unusable data: {e}")

    return prescription_data

@router.get("/analyze/{animal_id}")
async def get_animal_prescription_history(animal_id: str) -> Dict[str, Any]:
    """
    Get comprehensive prescription and treatment history for an animal
    """
    try:
        # Get comprehensive animal data from database
        animal_data = None
        if db_service and db_service.is_connected:
            animal_data = await db_service.get_animal(animal_id)
        
        # Query RAG for animal history
        rag_results = None
        try:
            from ..core.base import RAGRequest
            rag_request = RAGRequest(
                tag_no=animal_id,
                question=f"What are the prescriptions, treatments, medications and history for animal {animal_id}?"
            )
            rag_response = await rag_service.process(rag_request)
            rag_results = rag_response.answer if hasattr(rag_response, 'answer') else str(rag_response)
        except Exception as e:
            logger.warning(f"RAG query failed: {e}")
            rag_results = "No historical data available"
        
        # Get AMU usage summary
        try:
            amu_summary = {"status": "AMU service not available", "usage_data": []}
            if amu_agent and animal_data:
                # Analyze existing prescriptions for AMU
                prescriptions = animal_data.get("prescriptions", [])
                treatments = animal_data.get("treatments", [])
                amu_summary = await amu_agent.analyze_animal_usage(animal_id, prescriptions, treatments)
        except Exception as e:
            logger.warning(f"AMU summary failed: {e}")
            amu_summary = {"status": "AMU service error", "error": str(e)}
        
        # Get agent information
        try:
            amu_info = {"agent_name": "AMU Tracking Agent", "status": "available"}
            mrl_info = {"agent_name": "MRL Compliance Agent", "status": "available"}
            if amu_agent:
                amu_info = await amu_agent.get_agent_info()
            if mrl_agent:
                mrl_info = await mrl_agent.get_agent_info()
        except Exception as e:
            logger.warning(f"Agent info failed: {e}")
            amu_info = {"agent_name": "AMU Tracking Agent", "status": "error"}
            mrl_info = {"agent_name": "MRL Compliance Agent", "status": "error"}
        
        return {
            "status": "success",
            "animal_id": animal_id,
            "animal_data": animal_data,
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

@router.get("/animal/{tag_no}")
async def get_animal_by_tag(tag_no: str) -> Dict[str, Any]:
    """
    Get comprehensive animal data by tag number
    """
    try:
        if not db_service or not db_service.is_connected:
            raise HTTPException(status_code=503, detail="Database service not available")
        
        # Get animal data from database
        animal_data = await db_service.get_animal(tag_no)
        
        if not animal_data:
            raise HTTPException(status_code=404, detail=f"Animal with tag {tag_no} not found")
        
        # Get AMU analysis for all prescriptions
        amu_analysis = None
        if amu_agent and animal_data.get("prescriptions"):
            try:
                prescriptions = animal_data.get("prescriptions", [])
                treatments = animal_data.get("treatments", [])
                amu_analysis = await amu_agent.analyze_animal_usage(tag_no, prescriptions, treatments)
            except Exception as e:
                logger.warning(f"AMU analysis failed: {e}")
                amu_analysis = {"error": str(e)}
        
        return {
            "status": "success",
            "animal_data": animal_data,
            "amu_analysis": amu_analysis,
            "summary": {
                "total_prescriptions": len(animal_data.get("prescriptions", [])),
                "total_treatments": len(animal_data.get("treatments", [])),
                "created_at": animal_data.get("createdAt"),
                "updated_at": animal_data.get("updatedAt"),
                "species": animal_data.get("species", "Unknown")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving animal data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve animal data: {str(e)}")

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
    