# 🔍 Complete API Payload Validation Guide

## 📋 All API Endpoints and Their Payloads

### 🐄 **Animal Database Operations**

#### 1. Create Animal - `POST /database/animals`
```json
{
  "tagNo": "ANIMAL001",
  "breed": "Holstein",
  "gender": "Male",
  "farmId": "FARM123",
  "dateOfAdmission": "2025-09-14",
  "scanTag": "QR",
  "insurance": true,
  "vaccination": true,
  "artificialInsemination": false,
  "summary": "Healthy breeding animal",
  "complianceStatus": {
    "status": "OK",
    "lastUpdated": "2025-09-14T10:30:00Z"
  },
  "doctorVisits": [
    {
      "visitId": "VISIT_001",
      "doctorName": "Dr. Smith",
      "date": "2025-09-14T09:00:00Z",
      "purpose": "Routine checkup",
      "notes": "All vital signs normal"
    }
  ],
  "history": [
    {
      "date": "2025-09-14T08:00:00Z",
      "event": "health_check",
      "details": "Annual health checkup completed",
      "eventId": "HC_001",
      "category": "medical",
      "severity": "low",
      "cost": 150.0,
      "currency": "USD",
      "location": "Main barn",
      "weather": "Clear",
      "temperature": 72.5,
      "recordedBy": "Dr. Smith",
      "vetInvolved": true,
      "vetName": "Dr. Smith",
      "outcome": "successful",
      "followUpRequired": false,
      "notes": "Animal is in excellent health"
    },
    {
      "date": "2025-09-10T14:00:00Z",
      "event": "vaccination",
      "details": "Annual FMD vaccination administered",
      "eventId": "VAC_001",
      "category": "medical",
      "severity": "low",
      "cost": 45.0,
      "currency": "USD",
      "vetInvolved": true,
      "vetName": "Dr. Johnson",
      "outcome": "successful",
      "followUpRequired": true,
      "followUpDate": "2026-09-10",
      "notes": "Next vaccination due in 12 months"
    }
  ],
  "prescriptions": [
    {
      "prescriptionId": "PRESC_001",
      "doctorName": "Dr. Smith",
      "date": "2025-09-14T09:00:00Z",
      "vetId": "VET_001",
      "vetLicenseNumber": "VET123456",
      "vetClinic": "Farm Animal Health Center",
      "prescriptionType": "prevention",
      "diagnosis": "Healthy - routine supplementation",
      "reason": "Nutritional support during breeding season",
      "urgency": "low",
      "totalCost": 85.0,
      "currency": "USD",
      "paymentStatus": "paid",
      "followUpRequired": false,
      "ownerConsent": true,
      "status": "active",
      "medicines": [
        {
          "name": "Vitamin B Complex",
          "dosage": "5ml",
          "duration": "7 days",
          "frequency": "once daily",
          "medicineId": "MED_001",
          "manufacturer": "VetPharm Inc",
          "supplier": "Local Vet Supply",
          "batchNumber": "VB2025001",
          "expiryDate": "2026-12-31",
          "cost": 25.0,
          "currency": "USD",
          "totalQuantity": 35.0,
          "unit": "ml",
          "administrationRoute": "injection",
          "medicineType": "vitamin",
          "withdrawalPeriod": 0,
          "prescriptionRequired": true,
          "notes": "Administer intramuscularly"
        },
        {
          "name": "Selenium Supplement",
          "dosage": "10ml",
          "duration": "7 days",
          "frequency": "once daily",
          "medicineId": "MED_002",
          "manufacturer": "NutriVet",
          "cost": 60.0,
          "totalQuantity": 70.0,
          "unit": "ml",
          "administrationRoute": "oral",
          "medicineType": "vitamin",
          "withdrawalPeriod": 0
        }
      ]
    }
  ],
  "treatments": [
    {
      "treatmentId": "TREAT_001",
      "type": "Preventive Care",
      "startDate": "2025-09-14T09:00:00Z",
      "endDate": "2025-09-21T09:00:00Z",
      "status": "Active",
      "medication": "Vitamin Supplement",
      "treatmentName": "Routine Vitamin Supplementation",
      "category": "preventive",
      "subcategory": "nutrition",
      "priority": "low",
      "vetInCharge": "Dr. Smith",
      "vetId": "VET_001",
      "facility": "Farm Health Center",
      "diagnosis": "Healthy - nutritional support",
      "procedure": "Intramuscular injection of vitamins",
      "duration": "7 days",
      "frequency": "once daily",
      "effectiveness": "excellent",
      "outcome": "successful",
      "estimatedCost": 85.0,
      "actualCost": 85.0,
      "currency": "USD",
      "costBreakdown": {
        "medication": 85.0,
        "consultation": 0.0
      },
      "followUpRequired": false,
      "withdrawalPeriod": 0,
      "consentObtained": true,
      "notes": "Routine supplementation completed successfully"
    }
  ],
  "customField1": "Additional farm-specific data",
  "customField2": {
    "breeding_program": "Elite Holstein",
    "genetic_value": "High"
  }
}
```

#### 2. Create Animal (Simplified) - `POST /database/animals`
```json
{
  "tagNo": "ANIMAL002",
  "breed": "Jersey",
  "gender": "Female",
  "farmId": "FARM456",
  "dateOfAdmission": "2025-09-14",
  "summary": "Young female for dairy production",
  "history": [
    {
      "date": "2025-09-14T08:00:00Z",
      "event": "registration",
      "details": "Animal registered in system",
      "category": "administrative",
      "recordedBy": "Farm Manager"
    }
  ],
  "prescriptions": [
    {
      "doctorName": "Dr. Wilson",
      "date": "2025-09-14T10:00:00Z",
      "prescriptionType": "routine",
      "medicines": [
        {
          "name": "Calcium Supplement",
          "dosage": "10ml",
          "duration": "5 days",
          "frequency": "twice daily",
          "administrationRoute": "oral",
          "medicineType": "vitamin"
        }
      ]
    }
  ],
  "treatments": [
    {
      "type": "Health Check",
      "startDate": "2025-09-14T10:00:00Z",
      "status": "Completed",
      "category": "medical",
      "outcome": "successful",
      "notes": "Initial health assessment - all normal"
    }
  ]
}
```

#### 3. Update Animal - `PUT /database/animals/{tag_no}`
```json
{
  "breed": "Updated Holstein",
  "summary": "Updated animal information",
  "vaccination": true,
  "insurance": false
}
```

#### 3. Search Animals - `POST /database/animals/search`
```json
{
  "breed": "Holstein",
  "gender": "Male",
  "farmId": "FARM123"
}
```

---

### 🧠 **RAG (Retrieval Augmented Generation)**

#### 4. RAG Query - `POST /rag/ask`
```json
{
  "tag_no": "ANIMAL001",
  "question": "What is the health status of this animal?",
  "session_id": "session_123",
  "metadata": {
    "user_id": "user_456",
    "timestamp": "2025-09-14T10:30:00Z"
  }
}
```

---

### 💬 **Chat Service**

#### 5. Chat Query - `POST /chat/ask`
```json
{
  "message": "Tell me about animal health protocols",
  "conversation_history": [
    {
      "role": "user",
      "content": "What vaccines are recommended?"
    },
    {
      "role": "assistant", 
      "content": "Common vaccines include FMD, BVD, and IBR"
    }
  ],
  "session_id": "chat_session_789",
  "metadata": {
    "context": "veterinary_consultation"
  }
}
```

---

### 💊 **AMU (Antimicrobial Usage) Tracking**

#### 6. AMU Analysis - `POST /amu/analyze`
```json
{
  "animal_id": "ANIMAL001",
  "drug_name": "Penicillin G",
  "dosage": 20000.0,
  "frequency": "twice daily",
  "duration_days": 5,
  "treatment_date": "2025-09-14",
  "veterinarian_id": "VET001",
  "session_id": "amu_session_001"
}
```

#### 7. AMU Compliance Check - `POST /amu/compliance`
```json
{
  "animal_id": "ANIMAL001",
  "drug_name": "Penicillin G",
  "dosage": 20000.0,
  "frequency": "twice daily",
  "duration_days": 5,
  "treatment_date": "2025-09-14",
  "session_id": "compliance_check_001"
}
```

---

### 🧪 **MRL (Maximum Residue Limit) Compliance**

#### 8. MRL Check - `POST /mrl/check`
```json
{
  "animal_id": "ANIMAL001",
  "species": "Cattle",
  "drug_name": "Penicillin G",
  "last_treatment_date": "2025-09-14",
  "slaughter_date": "2025-09-30",
  "session_id": "mrl_check_001"
}
```

#### 9. Withdrawal Period Calculation - `POST /mrl/calculate-withdrawal`
```json
{
  "animal_id": "ANIMAL001",
  "species": "Cattle", 
  "drug_name": "Penicillin G",
  "last_treatment_date": "2025-09-14",
  "slaughter_date": "2025-09-30",
  "session_id": "withdrawal_calc_001"
}
```

#### 10. Residue Prediction - `POST /mrl/predict-residue`
```json
{
  "animal_id": "ANIMAL001",
  "species": "Cattle",
  "drug_name": "Penicillin G", 
  "dosage": 20000.0,
  "treatment_date": "2025-09-14",
  "prediction_date": "2025-09-30"
}
```

---

### 📋 **Prescription Analysis**

#### 11. Prescription Upload - `POST /prescription/upload`
```json
{
  "animal_id": "ANIMAL001",
  "farm_id": "FARM123",
  "prescription_notes": "Prescription for antibiotic treatment",
  "session_id": "prescription_upload_001"
}
```

---

### ⚠️ **Risk Prediction**

#### 12. Risk Prediction - `POST /risk/predict`
```json
{
  "age": 36,
  "weight": 550,
  "farm_size": 100,
  "previous_infections": 2,
  "treatment_duration": 5,
  "dosage": 20000,
  "time_since_last_treatment": 30,
  "previous_treatments": 3,
  "animal_type": "Cattle",
  "farm_type": "Dairy",
  "vaccination_status": "Up to date",
  "feed_type": "Commercial",
  "housing_condition": "Indoor",
  "region": "North",
  "season": "Spring",
  "antibiotic_class_used": "Beta-lactam",
  "resistance_pattern": "Sensitive",
  "session_id": "risk_prediction_001"
}
```

#### 13. Pattern Analysis - `POST /risk/analyze-patterns`
```json
{
  "analysis_type": "temporal",
  "region": "North",
  "time_period": "2025-Q3",
  "parameters": {
    "include_historical": true,
    "granularity": "monthly"
  },
  "session_id": "pattern_analysis_001"
}
```

#### 14. Model Update - `POST /risk/update-model`
```json
{
  "model_version": "2.1",
  "training_data_source": "latest_dataset",
  "parameters": {
    "learning_rate": 0.001,
    "epochs": 100
  },
  "session_id": "model_update_001"
}
```

#### 15. Prediction Explanation - `POST /risk/explain-prediction`
```json
{
  "prediction_id": "PRED_001",
  "animal_id": "ANIMAL001",
  "session_id": "explanation_001"
}
```

---

### 🐄 **Animal-Centric Unified API**

#### 16. Animal Chat - `POST /animal/{tag_no}/chat`
```json
{
  "message": "What medications has this animal received recently?",
  "conversation_id": "animal_chat_001",
  "context": {
    "include_history": true,
    "include_prescriptions": true
  }
}
```

---

## 🔧 **Enhanced Schema Documentation**

### **🔍 History Entry Fields**
The enhanced history entry supports comprehensive event tracking:

**Required Fields:**
- `date`: ISO timestamp of the event
- `event`: Event type (health_check, vaccination, treatment, birth, sale, injury, etc.)
- `details`: Detailed description of the event

**Enhanced Optional Fields:**
- `eventId`: Unique identifier for tracking
- `category`: Classification (medical, administrative, breeding, nutrition, behavioral)
- `severity`: Impact level (low, medium, high, critical)
- `cost`: Financial cost of the event
- `location`: Where the event occurred
- `weather`: Environmental conditions
- `temperature`: Environmental temperature
- `recordedBy`: Person who recorded the event
- `vetInvolved`: Whether a veterinarian was involved
- `vetName`: Name of the veterinarian
- `outcome`: Result (successful, failed, partial, pending)
- `followUpRequired`: Whether follow-up is needed
- `followUpDate`: When follow-up should occur
- `relatedEvents`: Links to related history entries
- `images`: Related photos or documents
- `notes`: Additional notes

### **💊 Prescription & Medicine Fields**
Enhanced prescription tracking includes:

**Medicine Fields:**
- `medicineId`: Unique medicine identifier
- `genericName` / `brandName`: Medicine identification
- `manufacturer` / `supplier`: Source information
- `batchNumber` / `expiryDate`: Quality control
- `cost` / `unitPrice`: Financial tracking
- `administrationRoute`: How medicine is given (oral, injection, topical)
- `medicineType`: Category (antibiotic, vaccine, vitamin, etc.)
- `activeIngredients`: List of active compounds
- `withdrawalPeriod`: Days before animal products are safe
- `sideEffects` / `contraindications`: Safety information
- `storageConditions`: How to store the medicine

**Prescription Fields:**
- `vetId` / `vetLicenseNumber`: Veterinarian identification
- `vetClinic` / `vetContactInfo`: Clinic information
- `prescriptionType`: Category (treatment, prevention, emergency, routine)
- `diagnosis`: Medical condition being treated
- `symptoms`: Observed symptoms
- `vitalSigns`: Health measurements
- `urgency`: Priority level (low, medium, high, emergency)
- `totalCost` / `paymentStatus`: Financial tracking
- `followUpRequired` / `followUpDate`: Care continuity
- `ownerConsent`: Authorization received
- `status`: Current state (active, completed, cancelled, expired)

### **🏥 Treatment Fields**
Comprehensive treatment tracking includes:

**Basic Treatment Info:**
- `treatmentName`: Descriptive name
- `category`: Type (medical, surgical, preventive, emergency)
- `priority`: Urgency level
- `vetInCharge`: Primary veterinarian
- `facility`: Treatment location

**Medical Details:**
- `diagnosis` / `preDiagnosis`: Medical conditions
- `symptoms`: Observed symptoms
- `vitalSignsBefore` / `vitalSignsAfter`: Health measurements
- `procedure`: What was done
- `anesthesiaUsed` / `anesthesiaType`: Anesthesia information
- `medicationsUsed` / `dosages`: Medicines administered

**Outcomes & Monitoring:**
- `effectiveness`: How well treatment worked (excellent, good, fair, poor)
- `outcome`: Final result (successful, partial_success, failed, ongoing)
- `complications` / `sideEffects`: Problems encountered
- `recoveryTime`: How long recovery took
- `monitoringRequired`: Whether ongoing monitoring is needed

**Financial & Documentation:**
- `estimatedCost` / `actualCost`: Budget vs actual
- `costBreakdown`: Detailed cost analysis
- `insuranceCovered` / `insuranceAmount`: Insurance information
- `beforeImages` / `afterImages`: Visual documentation
- `xrays` / `labResults`: Medical documentation

**Compliance & Safety:**
- `withdrawalPeriod`: Food safety compliance
- `reportableEvent`: Whether authorities must be notified
- `consentObtained`: Owner authorization
- `ethicsApproval`: Research compliance if applicable

---

## 🔧 **Validation Rules Summary**

### **Required Fields by Endpoint:**

#### Animal Creation:
- `tagNo`: String (unique)
- `breed`: String  
- `gender`: "Male" or "Female"
- `farmId`: String

#### RAG Requests:
- `tag_no`: String
- `question`: String

#### AMU Requests:
- `animal_id`: String
- `drug_name`: String
- `dosage`: Number
- `frequency`: String
- `duration_days`: Integer
- `treatment_date`: String (ISO date)

#### MRL Requests:
- `animal_id`: String
- `species`: String
- `drug_name`: String
- `last_treatment_date`: String (ISO date)

#### Risk Prediction:
- All 17 fields are required (age, weight, farm_size, etc.)

### **Common Optional Fields:**
- `session_id`: String
- `metadata`: Object
- `conversation_history`: Array
- `slaughter_date`: String (ISO date)

### **Date Format Requirements:**
- ISO 8601 format: `"2025-09-14T10:30:00Z"`
- Simple date: `"2025-09-14"`

### **Data Type Validation:**
- **Strings**: tagNo, breed, gender, farmId, drug_name, etc.
- **Numbers**: dosage, weight, age, farm_size, risk_score
- **Integers**: duration_days, previous_infections, treatment_duration
- **Booleans**: insurance, vaccination, mrl_compliant
- **Arrays**: history, prescriptions, treatments, conversation_history
- **Objects**: complianceStatus, metadata, parameters

### **Enum Values:**
- **Gender**: "Male", "Female"
- **Status**: "OK", "Warning", "Critical"
- **Risk Level**: "Low", "Medium", "High"
- **Treatment Status**: "Active", "Completed", "Discontinued"

---

## ✅ **Testing All Payloads**

Use these exact payloads for testing - they include all required fields and proper data types. Each payload has been validated against the Pydantic models in the system.

**Server URL**: `http://localhost:8001`
**Documentation**: `http://localhost:8001/docs`

All payloads are production-ready and will pass validation! 🚀