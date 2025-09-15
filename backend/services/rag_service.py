# RAG Service Implementation
import os
import json
import pandas as pd
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..core.base import BaseService, RAGRequest, RAGResponse
from ..core.config import settings

class RAGService(BaseService):
    """RAG (Retrieval-Augmented Generation) Service for Animal Treatment Records"""
    
    def __init__(self, database_service=None):
        super().__init__("rag_service", "1.0.0")
        self.animal_db: Dict[str, Dict] = {}
        self.gemini_api_key = settings.gemini_api_key
        self.gemini_model = settings.gemini_model
        self.database_service = database_service
        self.use_mongodb = database_service is not None
        
    async def initialize(self) -> bool:
        """Initialize the RAG service"""
        try:
            # Try to use MongoDB first, fallback to CSV
            if self.database_service and hasattr(self.database_service, 'is_connected') and self.database_service.is_connected:
                await self._load_from_mongodb()
                self.logger.info("RAG Service using MongoDB for data")
            else:
                # Load animal database from CSV
                await self._load_animal_database()
                self.logger.info("RAG Service using CSV for data")
            
            # Set up API key
            os.environ["GEMINI_API_KEY"] = self.gemini_api_key
            
            self.is_initialized = True
            self.logger.info("RAG Service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG Service: {e}")
            return False
    
    async def _load_animal_database(self):
        """Load animal data from CSV"""
        try:
            if os.path.exists(settings.csv_data_path):
                df = pd.read_csv(settings.csv_data_path)
                
                for _, row in df.iterrows():
                    self.animal_db[row["animal_id"]] = {
                        "name": row.get("name", ""),
                        "species": row.get("species", ""),
                        "treatment_logs": row.get("treatment_logs", ""),
                        "prescriptions": row.get("prescriptions", ""),
                        "withdrawal_dates": row.get("withdrawal_dates", "")
                    }
                
                self.logger.info(f"Loaded {len(self.animal_db)} animal records")
            else:
                self.logger.warning(f"CSV file not found: {settings.csv_data_path}")
                
        except Exception as e:
            self.logger.error(f"Error loading animal database: {e}")
            raise
    
    async def _load_from_mongodb(self):
        """Load animal data from MongoDB"""
        try:
            if not self.database_service:
                raise ValueError("Database service not available")
                
            animals = await self.database_service.get_all_animals(limit=1000)
            
            for animal in animals:
                tag_no = animal.get("tagNo")
                if tag_no:
                    # Map MongoDB schema to internal format
                    self.animal_db[tag_no] = {
                        "tag_no": tag_no,
                        "breed": animal.get("breed", ""),
                        "gender": animal.get("gender", ""),
                        "farm_id": animal.get("farmId", ""),
                        "date_of_admission": animal.get("dateOfAdmission", ""),
                        "scan_tag": animal.get("scanTag", ""),
                        "insurance": animal.get("insurance", False),
                        "vaccination": animal.get("vaccination", False),
                        "artificial_insemination": animal.get("artificialInsemination", False),
                        "compliance_status": animal.get("complianceStatus", {}),
                        "summary": animal.get("summary", ""),
                        "doctor_visits": animal.get("doctorVisits", []),
                        "history": animal.get("history", []),
                        "prescriptions": animal.get("prescriptions", []),
                        "treatments": animal.get("treatments", []),
                        "created_at": animal.get("createdAt", ""),
                        "updated_at": animal.get("updatedAt", ""),
                        # Store the full MongoDB document for reference
                        "_mongodb_doc": animal
                    }
            
            self.logger.info(f"Loaded {len(self.animal_db)} animal records from MongoDB")
                
        except Exception as e:
            self.logger.error(f"Error loading from MongoDB: {e}")
            # Fallback to CSV
            await self._load_animal_database()
    
    async def _get_animal_record(self, tag_no: str) -> Optional[Dict]:
        """Get animal record by tag number (with MongoDB fallback)"""
        # First try in-memory cache
        if tag_no in self.animal_db:
            return self.animal_db[tag_no]
        
        # If using MongoDB and not found in cache, try MongoDB directly
        if self.database_service:
            try:
                mongo_record = await self.database_service.get_animal(tag_no)
                if mongo_record:
                    # Convert and cache the record for future use
                    processed_record = {
                        "tag_no": mongo_record.get("tagNo", ""),
                        "breed": mongo_record.get("breed", ""),
                        "gender": mongo_record.get("gender", ""),
                        "farm_id": mongo_record.get("farmId", ""),
                        "prescriptions": mongo_record.get("prescriptions", []),
                        "treatments": mongo_record.get("treatments", []),
                        "history": mongo_record.get("history", []),
                        "_mongodb_doc": mongo_record
                    }
                    self.animal_db[tag_no] = processed_record
                    return processed_record
            except Exception as e:
                self.logger.error(f"Error fetching from MongoDB: {e}")
        
        return None
    
    def _simple_retrieve(self, question: str, animal_record: Dict) -> List[str]:
        """Simple keyword-based retrieval"""
        question_lower = question.lower()
        relevant_data = []
        
        # Basic animal info
        if animal_record.get('tag_no'):
            relevant_data.append(f"Animal Tag: {animal_record['tag_no']}")
        if animal_record.get('breed'):
            relevant_data.append(f"Breed: {animal_record['breed']}")
        if animal_record.get('gender'):
            relevant_data.append(f"Gender: {animal_record['gender']}")
        if animal_record.get('farm_id'):
            relevant_data.append(f"Farm ID: {animal_record['farm_id']}")
        
        # Treatment and medication related
        if any(word in question_lower for word in ['treatment', 'medication', 'medicine', 'drug', 'prescription']):
            treatments = animal_record.get('treatments', [])
            if treatments:
                relevant_data.append(f"Treatments: {treatments}")
            
            prescriptions = animal_record.get('prescriptions', [])
            if prescriptions:
                relevant_data.append(f"Prescriptions: {prescriptions}")
        
        # Health history
        if any(word in question_lower for word in ['history', 'health', 'medical', 'past']):
            history = animal_record.get('history', [])
            if history:
                relevant_data.append(f"Medical history: {history}")
        
        # Vaccination and compliance
        if any(word in question_lower for word in ['vaccine', 'vaccination', 'compliance']):
            if 'vaccination' in animal_record:
                relevant_data.append(f"Vaccination status: {animal_record['vaccination']}")
            if 'compliance_status' in animal_record:
                relevant_data.append(f"Compliance status: {animal_record['compliance_status']}")
        
        # Doctor visits
        if any(word in question_lower for word in ['doctor', 'visit', 'consultation', 'checkup']):
            doctor_visits = animal_record.get('doctor_visits', [])
            if doctor_visits:
                relevant_data.append(f"Doctor visits: {doctor_visits}")
        
        return relevant_data
    
    def _build_prompt(self, record: Dict, retrieved_data: List[str], question: str) -> str:
        """Build prompt for Gemini API"""
        prompt = f"""You are AMU-Trace, an expert assistant for animal treatment records. 
Your task is to provide accurate, concise, and context-aware answers based on the records provided. 

Animal Information:
- Tag Number: {record.get('tag_no', 'Unknown')}
- Breed: {record.get('breed', 'Unknown')}
- Gender: {record.get('gender', 'Unknown')}
- Farm ID: {record.get('farm_id', 'Unknown')}

Available Record Data:
- Treatments: {record.get('treatments', 'None available')}
- Prescriptions: {record.get('prescriptions', 'None available')}
- Medical History: {record.get('history', 'None available')}
- Vaccination Status: {record.get('vaccination', 'Not specified')}
- Compliance Status: {record.get('compliance_status', 'Not specified')}

Retrieved Information:
{chr(10).join(retrieved_data) if retrieved_data else 'No specific data retrieved for this question.'}

Question: {question}

Instructions:
1. Answer based only on the provided record data
2. If information is not available, clearly state so
3. For treatment or medication questions, provide specific details if available
4. Be professional and clear in your response
5. If the question is unclear or ambiguous, ask for clarification

Answer:"""
        return prompt
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent"
            headers = {"x-goog-api-key": self.gemini_api_key, "Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 503:
                return "The Gemini API is currently overloaded. Please try again in a few moments."
            elif response.status_code != 200:
                return f"API Error ({response.status_code}): Unable to get response. Please try again."
            
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            
        except Exception as e:
            self.logger.error(f"Error calling Gemini API: {e}")
            return f"Error connecting to Gemini API: {str(e)}"
    
    async def process(self, request: RAGRequest) -> RAGResponse:
        """Process RAG request"""
        try:
            # Get animal record
            record = await self._get_animal_record(request.tag_no)
            if not record:
                return RAGResponse(
                    success=False,
                    message="Animal not found",
                    error="Animal tag not found in database",
                    service_name=self.name,
                    timestamp=datetime.now().isoformat(),
                    tag_no=request.tag_no,
                    breed="",
                    gender="",
                    question=request.question,
                    answer="Animal not found. Please check the tag number."
                )
            
            # Retrieve relevant information
            retrieved_data = self._simple_retrieve(request.question, record)
            
            # Build prompt and get answer
            prompt = self._build_prompt(record, retrieved_data, request.question)
            answer = await self._call_gemini(prompt)
            
            return RAGResponse(
                success=True,
                message="RAG query processed successfully",
                service_name=self.name,
                timestamp=datetime.now().isoformat(),
                tag_no=request.tag_no,
                breed=record.get("breed", ""),
                gender=record.get("gender", ""),
                question=request.question,
                answer=answer
            )
            
        except Exception as e:
            self.logger.error(f"Error processing RAG request: {e}")
            return RAGResponse(
                success=False,
                message="Error processing request",
                error=str(e),
                service_name=self.name,
                timestamp=datetime.now().isoformat(),
                animal_id=request.animal_id,
                animal_name="",
                species="",
                question=request.question,
                answer="An error occurred while processing your request."
            )

    async def refine_text_with_gemini(self, text: str, instruction: str = "Clean and normalize this prescription text for structured parsing.") -> str:
        """Use Gemini to refine and normalize extracted OCR text for better parsing.

        This method builds a small prompt around the instruction and returns refined text.
        """
        try:
            prompt = f"Instruction: {instruction}\n\nText:\n{text}\n\nRefined Text:" 
            response = await self._call_gemini(prompt)
            # If Gemini returns a descriptive answer, try to extract the refined text part
            return response.strip()
        except Exception as e:
            self.logger.error(f"Error refining text with Gemini: {e}")
            return text
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        return {
            "service": self.name,
            "version": self.version,
            "status": "healthy" if self.is_initialized else "unhealthy",
            "animals_loaded": len(self.animal_db),
            "gemini_api_configured": bool(self.gemini_api_key),
            "csv_path_exists": os.path.exists(settings.csv_data_path)
        }
    
    def get_all_animals(self) -> Dict[str, Any]:
        """Get all animal IDs and basic info"""
        return {
            "total_count": len(self.animal_db),
            "animal_ids": list(self.animal_db.keys())
        }
    
    async def get_animal_info(self, animal_id: str) -> Optional[Dict]:
        """Get detailed animal information"""
        record = await self._get_animal_record(animal_id)
        if record:
            return {
                "animal_id": animal_id,
                **record
            }
        return None