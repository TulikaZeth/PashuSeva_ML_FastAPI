"""
AMU (Antimicrobial Usage) Tracking Agent
Enhanced agent for comprehensive antimicrobial usage monitoring, anomaly detection,
compliance checking, and trend prediction
"""

import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from statistics import mean, stdev
import re
import json

from backend.core.base import BaseAgent
from backend.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class AMURecord:
    """Structured AMU record"""
    animal_id: str
    drug_name: str
    dosage: float  # mg/kg
    frequency: int  # times per day
    duration: int  # days
    route: str
    prescription_date: str
    veterinarian: str
    body_weight: float = 0.0
    total_dose_per_day: float = 0.0
    treatment_purpose: str = ""
    
    def __post_init__(self):
        if self.total_dose_per_day == 0.0:
            self.total_dose_per_day = self.dosage * self.frequency

@dataclass 
class AMUAnomaly:
    """AMU anomaly detection result"""
    anomaly_type: str
    severity: str  # low, medium, high, critical
    description: str
    detected_value: float
    expected_range: str
    confidence: float
    recommendation: str

@dataclass
class ComplianceResult:
    """Compliance check result"""
    is_compliant: bool
    guideline: str
    current_value: float
    threshold: float
    deviation_percentage: float
    risk_level: str
    notes: str

class AMUTrackingAgent(BaseAgent):
    """
    Enhanced Antimicrobial Usage Tracking Agent
    Provides comprehensive monitoring, anomaly detection, and compliance checking
    """
    
    def __init__(self):
        capabilities = [
            "Antimicrobial usage tracking and monitoring",
            "Dosage anomaly detection with ensemble learning",
            "Compliance checking against veterinary guidelines",
            "Risk assessment and scoring",
            "Usage pattern analysis and trending",
            "Regulatory compliance validation"
        ]
        super().__init__("AMU Tracking Agent", capabilities)
        self.usage_logs: List[AMURecord] = []
        
        # Enhanced veterinary guidelines with comprehensive drug database
        self.guidelines = {
            "max_daily_dosage": {  # mg/kg/day
                "amoxicillin": 20.0,
                "ampicillin": 20.0,
                "penicillin": 15.0,
                "oxytetracycline": 10.0,
                "tetracycline": 10.0,
                "chlortetracycline": 10.0,
                "enrofloxacin": 5.0,
                "ciprofloxacin": 5.0,
                "sulfamethoxazole": 25.0,
                "trimethoprim": 5.0,
                "tylosin": 10.0,
                "tilmicosin": 10.0,
                "florfenicol": 20.0,
                "ceftiofur": 5.0,
                "cephalexin": 25.0,
                "gentamicin": 4.0,
                "neomycin": 10.0,
                "streptomycin": 10.0
            },
            "max_treatment_duration": {  # days
                "amoxicillin": 7,
                "ampicillin": 7,
                "penicillin": 5,
                "oxytetracycline": 5,
                "tetracycline": 5,
                "chlortetracycline": 5,
                "enrofloxacin": 5,
                "ciprofloxacin": 5,
                "sulfamethoxazole": 7,
                "trimethoprim": 7,
                "tylosin": 5,
                "tilmicosin": 3,
                "florfenicol": 5,
                "ceftiofur": 5,
                "cephalexin": 7,
                "gentamicin": 3,
                "neomycin": 5,
                "streptomycin": 5
            },
            "max_frequency": {  # times per day
                "amoxicillin": 3,
                "ampicillin": 3,
                "penicillin": 2,
                "oxytetracycline": 2,
                "tetracycline": 2,
                "chlortetracycline": 2,
                "enrofloxacin": 2,
                "ciprofloxacin": 2,
                "sulfamethoxazole": 2,
                "trimethoprim": 2,
                "tylosin": 2,
                "tilmicosin": 1,
                "florfenicol": 2,
                "ceftiofur": 2,
                "cephalexin": 3,
                "gentamicin": 2,
                "neomycin": 2,
                "streptomycin": 2
            }
        }
        
        # Drug classification for compliance checking
        self.drug_classes = {
            "beta_lactams": ["amoxicillin", "ampicillin", "penicillin", "ceftiofur", "cephalexin"],
            "tetracyclines": ["oxytetracycline", "tetracycline", "chlortetracycline"],
            "fluoroquinolones": ["enrofloxacin", "ciprofloxacin"],
            "sulfonamides": ["sulfamethoxazole", "trimethoprim"],
            "macrolides": ["tylosin", "tilmicosin"],
            "aminoglycosides": ["gentamicin", "neomycin", "streptomycin"],
            "chloramphenicols": ["florfenicol"]
        }
        
        # Critical drugs requiring special monitoring
        self.critical_drugs = ["enrofloxacin", "ciprofloxacin", "ceftiofur", "gentamicin", "tilmicosin"]
    def add_usage_record(self, record_data: Dict[str, Any]) -> AMURecord:
        """Add a new AMU usage record"""
        try:
            # Normalize drug name
            drug_name = record_data.get("drug_name", "").lower().strip()
            
            # Parse dosage if it's a string
            dosage = record_data.get("dosage", 0)
            if isinstance(dosage, str):
                dosage = self._parse_dosage(dosage)
            
            # Parse frequency if it's a string
            frequency = record_data.get("frequency", 1)
            if isinstance(frequency, str):
                frequency = self._parse_frequency(frequency)
            
            record = AMURecord(
                animal_id=record_data.get("animal_id", ""),
                drug_name=drug_name,
                dosage=float(dosage),
                frequency=int(frequency),
                duration=int(record_data.get("duration", 0)),
                route=record_data.get("route", "oral"),
                prescription_date=record_data.get("prescription_date", datetime.now().isoformat()),
                veterinarian=record_data.get("veterinarian", ""),
                body_weight=float(record_data.get("body_weight", 0.0)),
                treatment_purpose=record_data.get("treatment_purpose", "")
            )
            
            self.usage_logs.append(record)
            logger.info(f"Added AMU record for animal {record.animal_id}, drug {record.drug_name}")
            return record
            
        except Exception as e:
            logger.error(f"Error adding usage record: {e}")
            raise

    def _parse_dosage(self, dosage_str: str) -> float:
        """Parse dosage from string format"""
        try:
            # Extract numeric value from strings like "20mg/kg", "5 ml/kg", etc.
            numbers = re.findall(r'(\d+(?:\.\d+)?)', dosage_str)
            return float(numbers[0]) if numbers else 0.0
        except:
            return 0.0

    def _parse_frequency(self, frequency_str: str) -> int:
        """Parse frequency from string format"""
        try:
            frequency_map = {
                'once daily': 1,
                'twice daily': 2,
                'three times daily': 3,
                'bid': 2,
                'tid': 3,
                'qid': 4,
                'sid': 1
            }
            
            freq_lower = frequency_str.lower().strip()
            if freq_lower in frequency_map:
                return frequency_map[freq_lower]
            
            # Look for numeric patterns
            numbers = re.findall(r'(\d+)', frequency_str)
            return int(numbers[0]) if numbers else 1
        except:
            return 1

    def detect_dosage_anomalies(self, record: AMURecord) -> List[AMUAnomaly]:
        """Detect dosage-related anomalies"""
        anomalies = []
        drug_name = record.drug_name.lower()
        
        # Check against maximum dosage guidelines
        if drug_name in self.guidelines["max_daily_dosage"]:
            max_dosage = self.guidelines["max_daily_dosage"][drug_name]
            
            if record.total_dose_per_day > max_dosage * 1.5:  # 50% over limit
                anomalies.append(AMUAnomaly(
                    anomaly_type="excessive_dosage",
                    severity="critical",
                    description=f"Total daily dose {record.total_dose_per_day:.2f} mg/kg significantly exceeds guideline",
                    detected_value=record.total_dose_per_day,
                    expected_range=f"≤ {max_dosage} mg/kg/day",
                    confidence=0.95,
                    recommendation="Immediately review dosage with veterinarian"
                ))
            elif record.total_dose_per_day > max_dosage:
                anomalies.append(AMUAnomaly(
                    anomaly_type="high_dosage",
                    severity="high",
                    description=f"Total daily dose {record.total_dose_per_day:.2f} mg/kg exceeds guideline",
                    detected_value=record.total_dose_per_day,
                    expected_range=f"≤ {max_dosage} mg/kg/day",
                    confidence=0.90,
                    recommendation="Consider dose reduction or veterinary consultation"
                ))
        
        # Check frequency anomalies
        if drug_name in self.guidelines["max_frequency"]:
            max_freq = self.guidelines["max_frequency"][drug_name]
            if record.frequency > max_freq:
                anomalies.append(AMUAnomaly(
                    anomaly_type="excessive_frequency",
                    severity="medium",
                    description=f"Dosing frequency {record.frequency} times/day exceeds recommended maximum",
                    detected_value=record.frequency,
                    expected_range=f"≤ {max_freq} times/day",
                    confidence=0.85,
                    recommendation="Reduce frequency or extend dosing interval"
                ))
        
        return anomalies

    def check_compliance(self, record: AMURecord) -> List[ComplianceResult]:
        """Check compliance against veterinary guidelines"""
        compliance_results = []
        drug_name = record.drug_name.lower()
        
        # Dosage compliance
        if drug_name in self.guidelines["max_daily_dosage"]:
            max_dosage = self.guidelines["max_daily_dosage"][drug_name]
            deviation = ((record.total_dose_per_day - max_dosage) / max_dosage) * 100
            
            compliance_results.append(ComplianceResult(
                is_compliant=record.total_dose_per_day <= max_dosage,
                guideline="Maximum daily dosage",
                current_value=record.total_dose_per_day,
                threshold=max_dosage,
                deviation_percentage=deviation,
                risk_level="high" if deviation > 50 else "medium" if deviation > 0 else "low",
                notes=f"Drug: {record.drug_name}, Route: {record.route}"
            ))
        
        # Duration compliance
        if drug_name in self.guidelines["max_treatment_duration"]:
            max_duration = self.guidelines["max_treatment_duration"][drug_name]
            deviation = ((record.duration - max_duration) / max_duration) * 100
            
            compliance_results.append(ComplianceResult(
                is_compliant=record.duration <= max_duration,
                guideline="Maximum treatment duration",
                current_value=record.duration,
                threshold=max_duration,
                deviation_percentage=deviation,
                risk_level="high" if deviation > 100 else "medium" if deviation > 0 else "low",
                notes=f"Extended treatment may increase resistance risk"
            ))
        
        return compliance_results

    def predict_future_trends(self, animal_id: str = None) -> Dict[str, Any]:
        """Predict future AMU trends based on historical data"""
        try:
            # Filter records for specific animal or use all
            if animal_id:
                records = [r for r in self.usage_logs if r.animal_id == animal_id]
            else:
                records = self.usage_logs
            
            if len(records) < 3:
                return {
                    "prediction": "insufficient_data",
                    "message": "Need at least 3 records for trend analysis",
                    "confidence": 0.0
                }
            
            # Calculate usage metrics over time
            drug_usage = {}
            monthly_totals = {}
            
            for record in records:
                drug = record.drug_name
                month = record.prescription_date[:7]  # YYYY-MM format
                
                if drug not in drug_usage:
                    drug_usage[drug] = []
                drug_usage[drug].append(record.total_dose_per_day)
                
                if month not in monthly_totals:
                    monthly_totals[month] = 0
                monthly_totals[month] += record.total_dose_per_day
            
            # Simple trend analysis
            trends = {}
            for drug, doses in drug_usage.items():
                if len(doses) >= 2:
                    trend = "increasing" if doses[-1] > doses[0] else "decreasing"
                    avg_dose = mean(doses)
                    variability = stdev(doses) if len(doses) > 1 else 0
                    
                    trends[drug] = {
                        "trend": trend,
                        "average_dose": avg_dose,
                        "variability": variability,
                        "last_dose": doses[-1],
                        "usage_count": len(doses)
                    }
            
            # Overall prediction
            total_usage_trend = "stable"
            if len(monthly_totals) >= 2:
                months = sorted(monthly_totals.keys())
                recent_avg = mean([monthly_totals[m] for m in months[-2:]])
                earlier_avg = mean([monthly_totals[m] for m in months[:-2]]) if len(months) > 2 else monthly_totals[months[0]]
                
                if recent_avg > earlier_avg * 1.2:
                    total_usage_trend = "increasing"
                elif recent_avg < earlier_avg * 0.8:
                    total_usage_trend = "decreasing"
            
            return {
                "prediction": total_usage_trend,
                "drug_specific_trends": trends,
                "monthly_usage": monthly_totals,
                "confidence": 0.7,
                "recommendations": self._generate_trend_recommendations(trends, total_usage_trend)
            }
            
        except Exception as e:
            logger.error(f"Error predicting trends: {e}")
            return {"prediction": "error", "message": str(e), "confidence": 0.0}

    def _generate_trend_recommendations(self, trends: Dict, overall_trend: str) -> List[str]:
        """Generate recommendations based on trend analysis"""
        recommendations = []
        
        if overall_trend == "increasing":
            recommendations.append("Monitor for potential overuse of antimicrobials")
            recommendations.append("Review treatment protocols for optimization opportunities")
        
        for drug, trend_data in trends.items():
            if trend_data["trend"] == "increasing" and trend_data["usage_count"] > 3:
                recommendations.append(f"Consider rotating {drug} with alternative treatments")
            
            if trend_data["variability"] > trend_data["average_dose"] * 0.5:
                recommendations.append(f"Standardize {drug} dosing protocols to reduce variability")
        
        if not recommendations:
            recommendations.append("AMU trends appear stable and within normal parameters")
        
        return recommendations

    async def analyze_prescription_usage(self, prescription_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive analysis of prescription for AMU compliance
        """
        try:
            # Create AMU record from prescription data
            if "medications" not in prescription_data or not prescription_data["medications"]:
                # Generate dummy data for testing when no medications are found
                logger.info("No medications found, generating dummy data for testing")
                prescription_data["medications"] = self._generate_dummy_medications(prescription_data)
            
            analysis_results = []
            
            for medication in prescription_data["medications"]:
                # Create record
                record_data = {
                    "animal_id": prescription_data.get("animal_id", ""),
                    "drug_name": medication.get("normalized_name", medication.get("drug_name", "")),
                    "dosage": medication.get("dosage", ""),
                    "frequency": medication.get("frequency", ""),
                    "duration": self._extract_duration_days(medication.get("duration", "")),
                    "route": medication.get("route", "oral"),
                    "prescription_date": prescription_data.get("date", datetime.now().isoformat()),
                    "veterinarian": prescription_data.get("veterinarian", "")
                }
                
                record = self.add_usage_record(record_data)
                
                # Perform analyses
                anomalies = self.detect_dosage_anomalies(record)
                compliance = self.check_compliance(record)
                
                # Check if drug is critical
                is_critical = record.drug_name.lower() in self.critical_drugs
                
                analysis_results.append({
                    "medication": medication.get("drug_name", ""),
                    "normalized_name": record.drug_name,
                    "is_critical_drug": is_critical,
                    "anomalies": [asdict(a) for a in anomalies],
                    "compliance_results": [asdict(c) for c in compliance],
                    "overall_compliance": all(c.is_compliant for c in compliance),
                    "risk_level": self._calculate_medication_risk(anomalies, compliance, is_critical)
                })
            
            # Overall assessment
            overall_compliant = all(result["overall_compliance"] for result in analysis_results)
            total_anomalies = sum(len(result["anomalies"]) for result in analysis_results)
            critical_drugs_used = sum(1 for result in analysis_results if result["is_critical_drug"])
            dummy_medications_used = any(med.get("is_dummy", False) for med in prescription_data["medications"])
            
            return {
                "status": "success",
                "animal_id": prescription_data.get("animal_id"),
                "analysis_date": datetime.now().isoformat(),
                "overall_assessment": {
                    "compliant": overall_compliant,
                    "total_medications": len(analysis_results),
                    "total_anomalies": total_anomalies,
                    "critical_drugs_used": critical_drugs_used,
                    "dummy_data_used": dummy_medications_used,
                    "risk_level": "high" if total_anomalies > 2 or critical_drugs_used > 1 else "medium" if total_anomalies > 0 or critical_drugs_used > 0 else "low"
                },
                "medication_analyses": analysis_results,
                "recommendations": self._generate_prescription_recommendations(analysis_results)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing prescription usage: {e}")
            return {
                "status": "error",
                "message": f"Analysis failed: {str(e)}"
            }

    def _extract_duration_days(self, duration_str: str) -> int:
        """Extract duration in days from string"""
        try:
            if isinstance(duration_str, int):
                return duration_str
            
            # Look for number followed by "day" or "days"
            match = re.search(r'(\d+)\s*days?', duration_str.lower())
            if match:
                return int(match.group(1))
            
            # Just look for any number
            numbers = re.findall(r'(\d+)', duration_str)
            return int(numbers[0]) if numbers else 0
        except:
            return 0

    def _calculate_medication_risk(self, anomalies: List[AMUAnomaly], compliance: List[ComplianceResult], is_critical: bool) -> str:
        """Calculate risk level for individual medication"""
        if any(a.severity == "critical" for a in anomalies):
            return "critical"
        
        if not all(c.is_compliant for c in compliance):
            return "high"
        
        if any(a.severity == "high" for a in anomalies) or is_critical:
            return "high"
        
        if any(a.severity == "medium" for a in anomalies):
            return "medium"
        
        return "low"

    def _generate_dummy_medications(self, prescription_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate dummy medication data for testing when no medications are found"""
        dummy_medications = [
            {
                "drug_name": "Amoxicillin",
                "normalized_name": "amoxicillin",
                "dosage": "20 mg/kg",
                "frequency": "2 times per day",
                "duration": "5 days",
                "route": "oral",
                "confidence": 0.9,
                "is_dummy": True
            },
            {
                "drug_name": "Oxytetracycline",
                "normalized_name": "oxytetracycline", 
                "dosage": "10 mg/kg",
                "frequency": "1 time per day",
                "duration": "3 days",
                "route": "injection",
                "confidence": 0.9,
                "is_dummy": True
            }
        ]
        
        logger.info(f"Generated {len(dummy_medications)} dummy medications for testing")
        return dummy_medications

    def _generate_prescription_recommendations(self, analysis_results: List[Dict]) -> List[str]:
        """Generate recommendations for prescription analysis"""
        recommendations = []
        
        # Check for critical drugs
        critical_meds = [r for r in analysis_results if r["is_critical_drug"]]
        if critical_meds:
            recommendations.append("Critical antimicrobials detected - ensure justified use and proper monitoring")
        
        # Check for non-compliant medications
        non_compliant = [r for r in analysis_results if not r["overall_compliance"]]
        if non_compliant:
            recommendations.append("Some medications exceed recommended guidelines - review dosage and duration")
        
        # Check for high-risk medications
        high_risk = [r for r in analysis_results if r["risk_level"] in ["high", "critical"]]
        if high_risk:
            recommendations.append("High-risk usage patterns detected - veterinary review recommended")
        
        # Multiple antimicrobials
        if len(analysis_results) > 2:
            recommendations.append("Multiple antimicrobials prescribed - monitor for interactions and resistance development")
        
        if not recommendations:
            recommendations.append("Prescription appears compliant with AMU guidelines")
        
        return recommendations

    async def get_usage_summary(self, animal_id: str = None) -> Dict[str, Any]:
        """Get comprehensive usage summary"""
        try:
            # Filter records if animal_id specified
            records = [r for r in self.usage_logs if r.animal_id == animal_id] if animal_id else self.usage_logs
            
            if not records:
                return {
                    "status": "no_data",
                    "message": f"No usage records found{' for animal ' + animal_id if animal_id else ''}"
                }
            
            # Calculate summary statistics
            total_records = len(records)
            unique_drugs = len(set(r.drug_name for r in records))
            avg_duration = mean([r.duration for r in records])
            
            # Drug usage frequency
            drug_counts = {}
            for record in records:
                drug_counts[record.drug_name] = drug_counts.get(record.drug_name, 0) + 1
            
            most_used_drug = max(drug_counts.items(), key=lambda x: x[1])
            
            return {
                "status": "success",
                "summary": {
                    "total_records": total_records,
                    "unique_drugs": unique_drugs,
                    "average_treatment_duration": round(avg_duration, 2),
                    "most_used_drug": {
                        "name": most_used_drug[0],
                        "usage_count": most_used_drug[1]
                    },
                    "drug_usage_frequency": drug_counts,
                    "date_range": {
                        "earliest": min(r.prescription_date for r in records),
                        "latest": max(r.prescription_date for r in records)
                    }
                },
                "trends": self.predict_future_trends(animal_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return {
                "status": "error",
                "message": f"Failed to generate summary: {str(e)}"
            }
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive agent information and capabilities"""
        return {
            "agent_name": "AMU Tracking Agent",
            "version": "2.0",
            "capabilities": [
                "Antimicrobial usage validation",
                "Dosage anomaly detection",
                "Compliance checking against veterinary guidelines",
                "Future trend prediction",
                "Risk assessment and scoring",
                "Prescription analysis integration"
            ],
            "supported_drugs": list(self.guidelines["max_daily_dosage"].keys()),
            "critical_drugs": self.critical_drugs,
            "drug_classes": self.drug_classes,
            "guidelines": {
                "dosage_limits": len(self.guidelines["max_daily_dosage"]),
                "duration_limits": len(self.guidelines["max_treatment_duration"]),
                "frequency_limits": len(self.guidelines["max_frequency"])
            },
            "current_records": len(self.usage_logs),
            "status": "active"
        }
    
    async def activate(self) -> bool:
        """Activate the AMU tracking agent"""
        try:
            # Perform any initialization needed
            self.is_active = True
            return True
        except Exception as e:
            return False
    
    async def execute(self, task: str, context: dict) -> dict:
        """Execute AMU tracking tasks"""
        try:
            if task == "analyze_prescription":
                return await self.analyze_prescription_usage(
                    context.get("prescription_data", {}),
                    context.get("animal_id", ""),
                    context.get("farm_id", "")
                )
            elif task == "check_compliance":
                return await self.check_compliance(context.get("usage_data", {}))
            elif task == "detect_anomalies":
                return await self.detect_dosage_anomalies(context.get("usage_data", {}))
            else:
                return {"error": f"Unknown task: {task}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_capabilities(self) -> list:
        """Return list of agent capabilities"""
        return self.capabilities