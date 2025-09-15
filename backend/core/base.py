# Base classes and interfaces for models and agents
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
import logging

# ==========================
# Base Request/Response Models
# ==========================
class BaseRequest(BaseModel):
    """Base request model for all services"""
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseResponse(BaseModel):
    """Base response model for all services"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    service_name: str
    timestamp: str

# ==========================
# Service-specific Models
# ==========================
class RAGRequest(BaseRequest):
    tag_no: str
    question: str

class RAGResponse(BaseResponse):
    tag_no: str
    breed: str
    gender: str
    question: str
    answer: str

class ChatRequest(BaseRequest):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseResponse):
    user_message: str
    response: str
    conversation_id: str

class AnalysisRequest(BaseRequest):
    data_type: str
    analysis_type: str
    parameters: Dict[str, Any]

class AnalysisResponse(BaseResponse):
    analysis_type: str
    results: Dict[str, Any]
    insights: List[str]

# ==========================
# AMU Tracking Models
# ==========================
class AMUTrackingRequest(BaseRequest):
    animal_id: str
    drug_name: str
    dosage: float
    frequency: str
    duration_days: int
    treatment_date: str
    veterinarian_id: Optional[str] = None

class AMUTrackingResponse(BaseResponse):
    animal_id: str
    compliance_status: str
    anomaly_detected: bool
    risk_score: float
    recommendations: List[str]

# ==========================
# MRL Compliance Models
# ==========================
class MRLComplianceRequest(BaseRequest):
    animal_id: str
    species: str
    drug_name: str
    last_treatment_date: str
    slaughter_date: Optional[str] = None

class MRLComplianceResponse(BaseResponse):
    animal_id: str
    mrl_compliant: bool
    withdrawal_period_days: int
    safe_date: str
    risk_level: str
    recommendations: List[str]

# ==========================
# Prescription Analysis Models  
# ==========================
class PrescriptionAnalysisRequest(BaseRequest):
    """Request model for prescription OCR + NLP analysis"""
    animal_id: str
    farm_id: Optional[str] = None
    
class PrescriptionUploadRequest(BaseRequest):
    """Request model for prescription image upload"""
    animal_id: str
    farm_id: Optional[str] = None
    prescription_notes: Optional[str] = None

class PrescriptionAnalysisResponse(BaseResponse):
    """Response model for prescription analysis"""
    animal_id: str
    extracted_text: str
    parsed_data: Dict[str, Any]
    drug_information: Dict[str, Any] 
    amu_analysis: Dict[str, Any]
    mrl_compliance: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    confidence_scores: Dict[str, float]

# ==========================
# Prescription Matching Models
# ==========================
class PrescriptionMatchingRequest(BaseRequest):
    prescription_image: Optional[str] = None  # Base64 encoded
    prescription_text: Optional[str] = None
    farm_log_data: Dict[str, Any]

class PrescriptionMatchingResponse(BaseResponse):
    extracted_data: Dict[str, Any]
    match_status: str
    discrepancies: List[str]
    confidence_score: float

# ==========================
# Risk Prediction Models
# ==========================
class RiskPredictionRequest(BaseRequest):
    age: int
    weight: int
    farm_size: int
    previous_infections: int
    treatment_duration: int
    dosage: int
    time_since_last_treatment: int
    previous_treatments: int
    animal_type: str
    farm_type: str
    vaccination_status: str
    feed_type: str
    housing_condition: str
    region: str
    season: str
    antibiotic_class_used: str
    resistance_pattern: str
    # Additional optional structures used by risk agent
    farm_id: Optional[str] = None
    farm_data: Optional[Dict[str, Any]] = None
    treatment_history: Optional[List[Dict[str, Any]]] = None
    historical_data: Optional[Dict[str, Any]] = None

class RiskPredictionResponse(BaseResponse):
    # Legacy field name expected by some clients
    amr_risk_level: Optional[str] = None
    # New/explicit category label
    risk_category: Optional[str] = None
    # Optional farm identifier echoed back in responses
    farm_id: Optional[str] = None
    risk_score: float
    # Allow structured risk factor breakdown (dict) rather than only list
    risk_factors: Optional[Dict[str, Any]] = None
    recommendations: List[str]

# ==========================
# Trend Analysis Models
# ==========================
class TrendAnalysisRequest(BaseRequest):
    analysis_type: str  # "regional", "temporal", "compliance"
    region: Optional[str] = None
    time_period: Optional[str] = None
    parameters: Dict[str, Any]

class TrendAnalysisResponse(BaseResponse):
    analysis_type: str
    trends: Dict[str, Any]
    insights: List[str]
    visualizations: List[str]

# ==========================
# Animal Database Models
# ==========================
class ComplianceStatus(BaseModel):
    status: str = "OK"
    lastUpdated: Optional[str] = None

class HistoryEntry(BaseModel):
    date: str
    event: str  # Event type: "health_check", "vaccination", "treatment", "birth", "sale", "death", "injury", "illness"
    details: str
    
    # Enhanced fields for better tracking
    eventId: Optional[str] = None
    category: Optional[str] = None  # "medical", "administrative", "breeding", "nutrition", "behavioral"
    severity: Optional[str] = None  # "low", "medium", "high", "critical"
    cost: Optional[float] = None
    currency: Optional[str] = "USD"
    location: Optional[str] = None  # Where the event occurred
    weather: Optional[str] = None  # Weather conditions during event
    temperature: Optional[float] = None  # Environmental temperature
    recordedBy: Optional[str] = None  # Who recorded this event
    vetInvolved: Optional[bool] = False
    vetName: Optional[str] = None
    outcome: Optional[str] = None  # "successful", "failed", "partial", "pending"
    followUpRequired: Optional[bool] = False
    followUpDate: Optional[str] = None
    relatedEvents: Optional[List[str]] = []  # IDs of related history entries
    images: Optional[List[str]] = []  # URLs or paths to related images
    documents: Optional[List[str]] = []  # URLs or paths to related documents
    notes: Optional[str] = None  # Additional notes

class DoctorVisit(BaseModel):
    visitId: Optional[str] = None
    doctorName: str  # Changed from 'veterinarian' to 'doctorName'
    date: str
    purpose: Optional[str] = None
    notes: Optional[str] = None

class Medicine(BaseModel):
    name: str
    dosage: str
    duration: str
    frequency: str
    
    # Enhanced fields for comprehensive medicine tracking
    medicineId: Optional[str] = None
    genericName: Optional[str] = None
    brandName: Optional[str] = None
    manufacturer: Optional[str] = None
    supplier: Optional[str] = None
    batchNumber: Optional[str] = None
    expiryDate: Optional[str] = None
    cost: Optional[float] = None
    currency: Optional[str] = "USD"
    unitPrice: Optional[float] = None
    totalQuantity: Optional[float] = None
    unit: Optional[str] = None  # "ml", "mg", "tablets", "doses"
    administrationRoute: Optional[str] = None  # "oral", "injection", "topical", "intravenous"
    medicineType: Optional[str] = None  # "antibiotic", "vaccine", "vitamin", "antiparasitic", "hormone"
    activeIngredients: Optional[List[str]] = []
    concentration: Optional[str] = None
    withdrawalPeriod: Optional[int] = None  # Days
    sideEffects: Optional[List[str]] = []
    contraindications: Optional[List[str]] = []
    storageConditions: Optional[str] = None
    prescriptionRequired: Optional[bool] = True
    controlledSubstance: Optional[bool] = False
    notes: Optional[str] = None

class Prescription(BaseModel):
    prescriptionId: Optional[str] = None
    doctorName: str  # Changed from 'veterinarian' to 'doctorName'
    date: str
    medicines: List[Medicine]  # Changed to support list of medicines
    
    # Enhanced fields for comprehensive prescription tracking
    vetId: Optional[str] = None
    vetLicenseNumber: Optional[str] = None
    vetClinic: Optional[str] = None
    vetContactInfo: Optional[str] = None
    prescriptionType: Optional[str] = None  # "treatment", "prevention", "emergency", "routine"
    diagnosis: Optional[str] = None
    symptoms: Optional[List[str]] = []
    vitalSigns: Optional[Dict[str, Any]] = None  # {"temperature": 101.5, "heart_rate": 60, "weight": 550}
    reason: Optional[str] = None
    urgency: Optional[str] = None  # "low", "medium", "high", "emergency"
    totalCost: Optional[float] = None
    currency: Optional[str] = "USD"
    paymentStatus: Optional[str] = None  # "paid", "pending", "insurance_claim", "unpaid"
    insuranceClaim: Optional[str] = None
    followUpRequired: Optional[bool] = False
    followUpDate: Optional[str] = None
    nextVisitDate: Optional[str] = None
    specialInstructions: Optional[str] = None
    ownerConsent: Optional[bool] = True
    regulatoryCompliance: Optional[Dict[str, Any]] = None
    prescriptionImage: Optional[str] = None  # URL or path to prescription image
    digitalSignature: Optional[str] = None
    validUntil: Optional[str] = None
    refillsAllowed: Optional[int] = 0
    status: Optional[str] = "active"  # "active", "completed", "cancelled", "expired"
    notes: Optional[str] = None

class Treatment(BaseModel):
    treatmentId: Optional[str] = None
    type: str  # Changed from 'treatment_type' to 'type'
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    status: Optional[str] = None
    medication: Optional[str] = None
    notes: Optional[str] = None
    
    # Enhanced fields for comprehensive treatment tracking
    treatmentName: Optional[str] = None
    category: Optional[str] = None  # "medical", "surgical", "preventive", "emergency", "routine"
    subcategory: Optional[str] = None  # "antibiotic_therapy", "surgery", "vaccination", "wound_care"
    priority: Optional[str] = None  # "low", "medium", "high", "emergency"
    vetInCharge: Optional[str] = None
    vetId: Optional[str] = None
    assistantVets: Optional[List[str]] = []
    facility: Optional[str] = None  # Where treatment was performed
    equipmentUsed: Optional[List[str]] = []
    
    # Medical details
    diagnosis: Optional[str] = None
    preDiagnosis: Optional[str] = None
    symptoms: Optional[List[str]] = []
    vitalSignsBefore: Optional[Dict[str, Any]] = None
    vitalSignsAfter: Optional[Dict[str, Any]] = None
    
    # Treatment specifics
    procedure: Optional[str] = None
    anesthesiaUsed: Optional[bool] = False
    anesthesiaType: Optional[str] = None
    medicationsUsed: Optional[List[str]] = []
    dosages: Optional[Dict[str, str]] = None
    administrationRoute: Optional[str] = None
    
    # Timeline and monitoring
    duration: Optional[str] = None  # "2 hours", "3 days", "1 week"
    frequency: Optional[str] = None  # "once daily", "twice daily", "as needed"
    monitoringRequired: Optional[bool] = False
    monitoringSchedule: Optional[str] = None
    
    # Outcomes and effectiveness
    effectiveness: Optional[str] = None  # "excellent", "good", "fair", "poor"
    outcome: Optional[str] = None  # "successful", "partial_success", "failed", "ongoing"
    complications: Optional[List[str]] = []
    sideEffects: Optional[List[str]] = []
    recoveryTime: Optional[str] = None
    
    # Financial tracking
    estimatedCost: Optional[float] = None
    actualCost: Optional[float] = None
    currency: Optional[str] = "USD"
    costBreakdown: Optional[Dict[str, float]] = None  # {"medication": 50, "procedure": 200, "consultation": 100}
    insuranceCovered: Optional[bool] = False
    insuranceAmount: Optional[float] = None
    
    # Follow-up and compliance
    followUpRequired: Optional[bool] = False
    followUpDate: Optional[str] = None
    followUpInstructions: Optional[str] = None
    complianceScore: Optional[float] = None  # 0-100%
    ownerInstructions: Optional[str] = None
    
    # Documentation
    beforeImages: Optional[List[str]] = []
    afterImages: Optional[List[str]] = []
    xrays: Optional[List[str]] = []
    labResults: Optional[List[str]] = []
    reports: Optional[List[str]] = []
    
    # Regulatory and safety
    withdrawalPeriod: Optional[int] = None  # Days
    reportableEvent: Optional[bool] = False
    regulatoryNotification: Optional[str] = None
    consentObtained: Optional[bool] = True
    ethicsApproval: Optional[str] = None

class AnimalCreateRequest(BaseModel):
    # Required fields
    tagNo: str
    breed: str
    gender: str  # "Male" or "Female"
    farmId: str
    
    # Optional fields
    dateOfAdmission: Optional[str] = None
    scanTag: Optional[str] = "QR"
    insurance: Optional[bool] = False
    vaccination: Optional[bool] = False
    artificialInsemination: Optional[bool] = False
    summary: Optional[str] = ""
    
    # Complex optional fields
    complianceStatus: Optional[ComplianceStatus] = None
    doctorVisits: Optional[List[DoctorVisit]] = []
    history: Optional[List[HistoryEntry]] = []
    prescriptions: Optional[List[Prescription]] = []
    treatments: Optional[List[Treatment]] = []
    
    # Custom fields - allows additional properties
    model_config = ConfigDict(extra="allow")  # This allows custom fields to be added

class AnimalUpdateRequest(BaseModel):
    # All fields optional for updates
    tagNo: Optional[str] = None
    breed: Optional[str] = None
    gender: Optional[str] = None
    farmId: Optional[str] = None
    dateOfAdmission: Optional[str] = None
    scanTag: Optional[str] = None
    insurance: Optional[bool] = None
    vaccination: Optional[bool] = None
    artificialInsemination: Optional[bool] = None
    summary: Optional[str] = None
    complianceStatus: Optional[ComplianceStatus] = None
    doctorVisits: Optional[List[DoctorVisit]] = None
    history: Optional[List[HistoryEntry]] = None
    prescriptions: Optional[List[Prescription]] = None
    treatments: Optional[List[Treatment]] = None
    
    # Custom fields - allows additional properties
    model_config = ConfigDict(extra="allow")  # This allows custom fields to be added

# ==========================
# Farmer Advisory Models
# ==========================
class FarmerAdvisoryRequest(BaseRequest):
    farmer_id: str
    farm_data: Dict[str, Any]
    current_issues: List[str]
    advisory_type: str  # "treatment", "prevention", "compliance"

class FarmerAdvisoryResponse(BaseResponse):
    farmer_id: str
    advisory_type: str
    recommendations: List[str]
    alerts: List[str]
    educational_content: List[str]

# ==========================
# Base Service Interface
# ==========================
class BaseService(ABC):
    """Abstract base class for all AI services"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.logger = logging.getLogger(f"service.{name}")
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the service (load models, setup connections, etc.)"""
        pass
    
    @abstractmethod
    async def process(self, request: BaseRequest) -> BaseResponse:
        """Process a request and return a response"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check service health and return status"""
        pass
    
    async def cleanup(self):
        """Cleanup resources when service is stopped"""
        self.logger.info(f"Cleaning up {self.name} service")

# ==========================
# Base Agent Interface  
# ==========================
class BaseAgent(ABC):
    """Abstract base class for all AI agents"""
    
    def __init__(self, name: str, capabilities: List[str], version: str = "1.0.0"):
        self.name = name
        self.capabilities = capabilities
        self.version = version
        self.logger = logging.getLogger(f"agent.{name}")
        self.is_active = False
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the agent (setup models, connections, etc.)"""
        try:
            result = await self.activate()
            self.is_initialized = result
            return result
        except Exception as e:
            self.logger.error(f"Failed to initialize agent {self.name}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the agent"""
        return {
            "status": "healthy" if self.is_active and self.is_initialized else "unhealthy",
            "agent": self.name,
            "version": self.version,
            "capabilities": self.capabilities,
            "is_active": self.is_active,
            "is_initialized": self.is_initialized
        }
    
    @abstractmethod
    async def activate(self) -> bool:
        """Activate the agent"""
        pass
    
    @abstractmethod
    async def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with given context"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass
    
    async def deactivate(self):
        """Deactivate the agent"""
        self.is_active = False
        self.is_initialized = False
        self.logger.info(f"Deactivated {self.name} agent")

# ==========================
# Model Manager Interface
# ==========================
class ModelManager(ABC):
    """Abstract base class for managing AI models"""
    
    def __init__(self, model_name: str, model_config: Dict[str, Any]):
        self.model_name = model_name
        self.model_config = model_config
        self.logger = logging.getLogger(f"model.{model_name}")
        self.model = None
        self.is_loaded = False
    
    @abstractmethod
    async def load_model(self) -> bool:
        """Load the AI model"""
        pass
    
    @abstractmethod
    async def predict(self, input_data: Any) -> Any:
        """Make prediction using the model"""
        pass
    
    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass
    
    async def unload_model(self):
        """Unload the model to free memory"""
        self.model = None
        self.is_loaded = False
        self.logger.info(f"Unloaded {self.model_name} model")

# ==========================
# End of file
# ==========================