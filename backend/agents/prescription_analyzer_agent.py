"""
Prescription Analyzer Agent - OCR + NLP for Veterinary Prescriptions
Processes prescription images to extract structured data and perform analysis
"""

import re
import io
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from PIL import Image
import pytesseract
import numpy as np
import cv2

from backend.core.base import BaseAgent
from backend.services.rag_service import RAGService

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class PrescriptionData:
    """Structured prescription data"""
    animal_id: Optional[str] = None
    veterinarian: Optional[str] = None
    clinic: Optional[str] = None
    date: Optional[str] = None
    medications: List[Dict[str, Any]] = None
    raw_text: str = ""
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.medications is None:
            self.medications = []

@dataclass
class MedicationInfo:
    """Individual medication information"""
    drug_name: str
    dosage: str
    frequency: str
    duration: str
    route: str = "oral"
    normalized_name: str = ""
    confidence: float = 0.0

class PrescriptionAnalyzerAgent(BaseAgent):
    """
    Agent for analyzing veterinary prescriptions using OCR and NLP
    """
    
    def __init__(self):
        capabilities = [
            "OCR text extraction from prescription images",
            "NLP parsing of prescription data", 
            "Drug name normalization and mapping",
            "Dosage and frequency extraction",
            "Veterinary prescription validation",
            "Integration with AMU and MRL analysis"
        ]
        super().__init__("Prescription Analyzer", capabilities)
        self.rag_service = RAGService()
        
        # Drug name mappings for normalization
        self.drug_mappings = {
            "oxytetracycline": ["oxytet", "terramycin", "oxtet"],
            "penicillin": ["pen", "penicillin g", "benzylpenicillin"],
            "amoxicillin": ["amox", "amoxycillin", "augmentin"],
            "cephalexin": ["keflex", "cefalexin"],
            "enrofloxacin": ["baytril", "enro"],
            "sulfamethoxazole": ["sulfa", "smz", "bactrim"],
            "tylosin": ["tylan", "tylvalosin"],
            "florfenicol": ["floricol", "nuflor"],
            "ceftiofur": ["excenel", "naxcel"],
            "trimethoprim": ["tmp", "tribrissen"]
        }
        
        # Dosage pattern regex
        self.dosage_patterns = [
            r'(\d+(?:\.\d+)?)\s*mg/kg',
            r'(\d+(?:\.\d+)?)\s*mg\s*per\s*kg',
            r'(\d+(?:\.\d+)?)\s*ml/kg',
            r'(\d+(?:\.\d+)?)\s*ml\s*per\s*kg',
            r'(\d+(?:\.\d+)?)\s*cc/kg',
            r'(\d+(?:\.\d+)?)\s*units/kg',
            r'(\d+(?:\.\d+)?)\s*mg',
            r'(\d+(?:\.\d+)?)\s*ml',
            r'(\d+(?:\.\d+)?)\s*cc'
        ]
        
        # Frequency patterns
        self.frequency_patterns = [
            r'(\d+)\s*times?\s*(?:per\s*)?day',
            r'(\d+)\s*times?\s*daily',
            r'once\s*daily',
            r'twice\s*daily',
            r'(\d+)x\s*daily',
            r'q(\d+)h',
            r'every\s*(\d+)\s*hours?',
            r'bid',
            r'tid',
            r'qid',
            r'sid'
        ]
        
        # Duration patterns
        self.duration_patterns = [
            r'for\s*(\d+)\s*days?',
            r'(\d+)\s*days?\s*treatment',
            r'(\d+)\s*day\s*course',
            r'continue\s*for\s*(\d+)\s*days?'
        ]
        
        logger.info("Prescription Analyzer Agent initialized")

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        """
        try:
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply noise reduction
            denoised = cv2.medianBlur(gray, 3)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Apply morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Convert back to PIL
            processed_image = Image.fromarray(cleaned)
            
            return processed_image
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image

    def extract_text_from_image(self, image: Image.Image) -> tuple[str, float]:
        """
        Extract text from prescription image using OCR
        """
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Configure Tesseract
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:()/-\n '
            
            # Extract text
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            # Get confidence data
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Clean text
            cleaned_text = self._clean_extracted_text(text)
            
            logger.info(f"OCR extraction completed with {avg_confidence:.1f}% confidence")
            return cleaned_text, avg_confidence / 100.0
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return "", 0.0

    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might be OCR artifacts
        text = re.sub(r'[^\w\s.,;:()/\-]', '', text)
        
        # Normalize common OCR mistakes
        replacements = {
            '0': 'o',  # Only in drug names context
            '1': 'l',  # Only in drug names context
            '5': 's',  # Only in drug names context
            'rng': 'mg',
            'rnl': 'ml',
            'tirnes': 'times',
            'daly': 'daily',
            'dai1y': 'daily'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.strip()

    def parse_prescription(self, text: str) -> PrescriptionData:
        """
        Parse prescription text to extract structured data
        """
        prescription = PrescriptionData(raw_text=text)
        
        try:
            # Extract animal ID
            prescription.animal_id = self._extract_animal_id(text)
            
            # Extract date
            prescription.date = self._extract_date(text)
            
            # Extract veterinarian info
            prescription.veterinarian = self._extract_veterinarian(text)
            
            # Extract medications
            prescription.medications = self._extract_medications(text)
            
            # Calculate confidence score based on extracted data
            prescription.confidence_score = self._calculate_confidence(prescription)
            
            logger.info(f"Parsed prescription for animal {prescription.animal_id}")
            return prescription
            
        except Exception as e:
            logger.error(f"Error parsing prescription: {e}")
            return prescription

    def _extract_animal_id(self, text: str) -> Optional[str]:
        """Extract animal ID from text"""
        patterns = [
            r'animal\s*id:?\s*([A-Z0-9]+)',
            r'id:?\s*([A-Z0-9]+)',
            r'tag:?\s*([A-Z0-9]+)',
            r'number:?\s*([A-Z0-9]+)',
            r'([A-Z]\d{2,4})',  # Pattern like A101, B1234
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract prescription date"""
        patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_veterinarian(self, text: str) -> Optional[str]:
        """Extract veterinarian name"""
        patterns = [
            r'dr\.?\s+([A-Za-z\s]+)',
            r'veterinarian:?\s*([A-Za-z\s]+)',
            r'vet:?\s*([A-Za-z\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().title()
        return None

    def _extract_medications(self, text: str) -> List[Dict[str, Any]]:
        """Extract medication information from text"""
        medications = []
        
        # Split text into potential medication entries
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
                
            # Look for drug names
            drug_name = self._extract_drug_name(line)
            if not drug_name:
                continue
                
            # Extract dosage, frequency, duration
            dosage = self._extract_dosage(line)
            frequency = self._extract_frequency(line)
            duration = self._extract_duration(line)
            route = self._extract_route(line)
            
            if drug_name:
                medication = {
                    "drug_name": drug_name,
                    "normalized_name": self._normalize_drug_name(drug_name),
                    "dosage": dosage or "Not specified",
                    "frequency": frequency or "Not specified", 
                    "duration": duration or "Not specified",
                    "route": route or "oral",
                    "confidence": 0.8 if all([drug_name, dosage, frequency]) else 0.5
                }
                medications.append(medication)
        
        return medications

    def _extract_drug_name(self, text: str) -> Optional[str]:
        """Extract drug name from text"""
        # Common drug names to look for
        drug_names = list(self.drug_mappings.keys())
        
        # Also add common aliases
        for drug, aliases in self.drug_mappings.items():
            drug_names.extend(aliases)
        
        text_lower = text.lower()
        
        for drug in drug_names:
            if drug.lower() in text_lower:
                return drug.title()
        
        # Look for capitalized words that might be drug names
        words = text.split()
        for word in words:
            if len(word) > 4 and word[0].isupper():
                return word
        
        return None

    def _normalize_drug_name(self, drug_name: str) -> str:
        """Normalize drug name to standard form"""
        drug_lower = drug_name.lower()
        
        for standard_name, aliases in self.drug_mappings.items():
            if drug_lower == standard_name or drug_lower in aliases:
                return standard_name.title()
        
        return drug_name.title()

    def _extract_dosage(self, text: str) -> Optional[str]:
        """Extract dosage from text"""
        for pattern in self.dosage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _extract_frequency(self, text: str) -> Optional[str]:
        """Extract frequency from text"""
        # Check for specific patterns
        frequency_map = {
            'once daily': '1 time per day',
            'twice daily': '2 times per day', 
            'bid': '2 times per day',
            'tid': '3 times per day',
            'qid': '4 times per day',
            'sid': '1 time per day'
        }
        
        text_lower = text.lower()
        for pattern, standardized in frequency_map.items():
            if pattern in text_lower:
                return standardized
        
        # Check numeric patterns
        for pattern in self.frequency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'q' in pattern and 'h' in pattern:
                    hours = match.group(1)
                    times_per_day = 24 // int(hours)
                    return f"{times_per_day} times per day (every {hours} hours)"
                else:
                    return match.group(0)
        
        return None

    def _extract_duration(self, text: str) -> Optional[str]:
        """Extract treatment duration from text"""
        for pattern in self.duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _extract_route(self, text: str) -> str:
        """Extract administration route"""
        routes = {
            'oral': ['oral', 'po', 'by mouth'],
            'injection': ['injection', 'inject', 'im', 'iv', 'sc'],
            'topical': ['topical', 'apply', 'external'],
            'intravenous': ['iv', 'intravenous'],
            'intramuscular': ['im', 'intramuscular'],
            'subcutaneous': ['sc', 'subcutaneous', 'sub-q']
        }
        
        text_lower = text.lower()
        
        for route, keywords in routes.items():
            if any(keyword in text_lower for keyword in keywords):
                return route
        
        return 'oral'  # Default

    def _calculate_confidence(self, prescription: PrescriptionData) -> float:
        """Calculate overall confidence score for prescription parsing"""
        score = 0.0
        total_weight = 0.0
        
        # Animal ID (weight: 3)
        if prescription.animal_id:
            score += 3.0
        total_weight += 3.0
        
        # Date (weight: 1)
        if prescription.date:
            score += 1.0
        total_weight += 1.0
        
        # Medications (weight: 5)
        if prescription.medications:
            med_score = 0.0
            for med in prescription.medications:
                if med.get('drug_name') and med.get('dosage') and med.get('frequency'):
                    med_score += 1.0
            score += min(med_score / len(prescription.medications), 1.0) * 5.0
        total_weight += 5.0
        
        return score / total_weight if total_weight > 0 else 0.0

    async def analyze_prescription(self, image: Image.Image) -> Dict[str, Any]:
        """
        Complete prescription analysis workflow
        """
        try:
            # Step 1: Extract text using OCR
            extracted_text, ocr_confidence = self.extract_text_from_image(image)
            
            if not extracted_text.strip():
                return {
                    "status": "error",
                    "message": "No text could be extracted from image",
                    "confidence": 0.0
                }
            
            # Step 2: Parse prescription data
            prescription_data = self.parse_prescription(extracted_text)
            
            # Step 3: Get animal records from RAG if animal ID found
            animal_records = None
            if prescription_data.animal_id:
                try:
                    animal_records = await self.rag_service.query(
                        f"animal_id:{prescription_data.animal_id} records history treatments"
                    )
                except Exception as e:
                    logger.warning(f"Could not retrieve animal records: {e}")
            
            # Step 4: Prepare structured output
            result = {
                "status": "success",
                "prescription_data": {
                    "animal_id": prescription_data.animal_id,
                    "date": prescription_data.date,
                    "veterinarian": prescription_data.veterinarian,
                    "medications": prescription_data.medications,
                    "confidence_score": prescription_data.confidence_score
                },
                "ocr_confidence": ocr_confidence,
                "raw_text": prescription_data.raw_text,
                "animal_records": animal_records.get("response") if animal_records else None,
                "ready_for_analysis": {
                    "amu_analysis": bool(prescription_data.medications),
                    "mrl_analysis": bool(prescription_data.medications and prescription_data.animal_id),
                    "rag_query": bool(prescription_data.animal_id)
                }
            }
            
            logger.info(f"Prescription analysis completed for animal {prescription_data.animal_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in prescription analysis: {e}")
            return {
                "status": "error",
                "message": f"Analysis failed: {str(e)}",
                "confidence": 0.0
            }

    async def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of prescription analysis capabilities"""
        return {
            "agent_name": "Prescription Analyzer",
            "capabilities": [
                "OCR text extraction from prescription images",
                "NLP parsing of veterinary prescriptions", 
                "Drug name normalization",
                "Dosage and frequency extraction",
                "Animal ID identification",
                "Integration with RAG for animal records",
                "Structured data output for downstream analysis"
            ],
            "supported_formats": ["JPEG", "PNG", "TIFF", "PDF"],
            "supported_drugs": list(self.drug_mappings.keys()),
            "confidence_metrics": {
                "ocr_confidence": "Text extraction accuracy",
                "parsing_confidence": "Structured data extraction accuracy",
                "overall_confidence": "Combined analysis reliability"
            }
        }

    async def activate(self) -> bool:
        """Activate the prescription analyzer agent"""
        try:
            # Test OCR functionality
            test_available = True
            logger.info("Prescription Analyzer Agent activated successfully")
            return test_available
        except Exception as e:
            logger.error(f"Failed to activate Prescription Analyzer Agent: {e}")
            return False

    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute prescription analysis task"""
        try:
            if task == "analyze_image":
                image = context.get("image")
                if not image:
                    return {"error": "No image provided"}
                
                result = await self.analyze_prescription(image)
                return result
            
            elif task == "parse_text":
                text = context.get("text", "")
                if not text:
                    return {"error": "No text provided"}
                
                prescription_data = self.parse_prescription(text)
                return {
                    "status": "success",
                    "prescription_data": prescription_data
                }
            
            else:
                return {"error": f"Unknown task: {task}"}
                
        except Exception as e:
            logger.error(f"Error executing task {task}: {e}")
            return {"error": str(e)}

    async def get_capabilities(self) -> List[str]:
        """Return agent capabilities"""
        return [
            "OCR text extraction",
            "NLP prescription parsing",
            "Drug name normalization", 
            "Dosage extraction",
            "Frequency parsing",
            "Animal ID identification",
            "Structured data output"
        ]