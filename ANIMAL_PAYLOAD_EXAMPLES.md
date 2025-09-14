# Complete Animal Creation Payload Examples

## 🐄 Comprehensive Animal Payload (All Fields)

```json
{
  "tagNo": "2428CS2015",
  "breed": "Holstein Friesian",
  "gender": "Male",
  "farmId": "OKVBHV",
  "dateOfAdmission": "2024-07-09",
  "scanTag": "QR",
  "insurance": true,
  "vaccination": true,
  "artificialInsemination": false,
  "summary": "Healthy bull, good breeding stock with excellent milk production lineage",
  
  "complianceStatus": {
    "status": "OK",
    "lastUpdated": "2025-09-14T10:30:00Z"
  },
  
  "doctorVisits": [
    {
      "visitId": "VISIT_001",
      "doctorName": "Dr. Sarah Johnson",
      "date": "2025-09-01T09:00:00Z",
      "purpose": "Routine Health Checkup",
      "notes": "Animal appears healthy, normal vital signs, recommended mineral supplements"
    },
    {
      "visitId": "VISIT_002", 
      "doctorName": "Dr. Michael Chen",
      "date": "2025-09-10T14:30:00Z",
      "purpose": "Fever Treatment Follow-up",
      "notes": "Temperature normalized, appetite returned, full recovery achieved"
    }
  ],
  
  "history": [
    {
      "date": "2024-07-09T08:00:00Z",
      "event": "Registration",
      "details": "Animal registered in farm management system, assigned tag number 2428CS2015"
    },
    {
      "date": "2024-07-15T10:30:00Z",
      "event": "Vaccination",
      "details": "Administered FMD (Foot and Mouth Disease) vaccination, batch number VAC-2024-789"
    },
    {
      "date": "2024-08-20T16:45:00Z",
      "event": "Health Issue",
      "details": "Observed mild fever symptoms (102.5°F), reduced appetite, isolated for monitoring"
    },
    {
      "date": "2024-08-21T09:15:00Z",
      "event": "Treatment Started",
      "details": "Started antibiotic treatment with Penicillin G, administered paracetamol for fever reduction"
    },
    {
      "date": "2024-08-25T11:00:00Z",
      "event": "Recovery",
      "details": "Full recovery achieved, temperature normal (100.8°F), appetite restored, returned to herd"
    },
    {
      "date": "2025-01-15T13:20:00Z",
      "event": "Breeding Assessment",
      "details": "Evaluated for breeding potential, excellent genetic markers identified, approved for breeding program"
    },
    {
      "date": "2025-09-01T09:00:00Z",
      "event": "Routine Checkup",
      "details": "Quarterly health assessment completed, all parameters within normal range"
    }
  ],
  
  "prescriptions": [
    {
      "prescriptionId": "PRESC_001",
      "doctorName": "Dr. Sarah Johnson",
      "date": "2024-08-21T09:15:00Z",
      "medicines": [
        {
          "name": "Penicillin G",
          "dosage": "20,000 IU/kg",
          "duration": "5 days",
          "frequency": "twice daily (12-hour intervals)"
        },
        {
          "name": "Paracetamol",
          "dosage": "15mg/kg",
          "duration": "3 days",
          "frequency": "every 8 hours"
        }
      ]
    },
    {
      "prescriptionId": "PRESC_002",
      "doctorName": "Dr. Michael Chen",
      "date": "2025-09-01T09:00:00Z",
      "medicines": [
        {
          "name": "Vitamin B-Complex",
          "dosage": "5ml",
          "duration": "7 days",
          "frequency": "once daily"
        },
        {
          "name": "Mineral Supplement",
          "dosage": "50g",
          "duration": "30 days",
          "frequency": "mixed with feed daily"
        }
      ]
    }
  ],
  
  "treatments": [
    {
      "treatmentId": "TREAT_001",
      "type": "Antibiotic Therapy",
      "startDate": "2024-08-21T09:15:00Z",
      "endDate": "2024-08-26T09:15:00Z",
      "status": "Completed",
      "medication": "Penicillin G + Paracetamol",
      "notes": "Treatment for bacterial infection and fever, successful recovery achieved"
    },
    {
      "treatmentId": "TREAT_002",
      "type": "Nutritional Support",
      "startDate": "2025-09-01T09:00:00Z",
      "endDate": "2025-10-01T09:00:00Z",
      "status": "Ongoing",
      "medication": "Vitamin B-Complex + Mineral Supplement",
      "notes": "Preventive nutritional therapy to maintain optimal health and productivity"
    }
  ],
  
  "customField1": "High Priority Breeding Stock",
  "customField2": "Lineage: Champion Bloodline",
  "specialNotes": "Exceptional animal with superior genetic markers for milk production",
  "lastWeighingDate": "2025-09-01",
  "currentWeight": "650kg",
  "expectedLifespan": "12-15 years"
}
```

## 🔬 Minimal Required Payload (Only Required Fields)

```json
{
  "tagNo": "SIMPLE001",
  "breed": "Jersey",
  "gender": "Female",
  "farmId": "FARM123"
}
```

## 🏥 Medical History Focused Payload

```json
{
  "tagNo": "MED2025001",
  "breed": "Angus",
  "gender": "Female",
  "farmId": "MEDICAL_FARM",
  "dateOfAdmission": "2025-01-15",
  "insurance": true,
  "vaccination": true,
  "summary": "High-value breeding cow with detailed medical tracking",
  
  "history": [
    {
      "date": "2025-01-15T08:00:00Z",
      "event": "Admission",
      "details": "Animal admitted to farm with complete health screening and documentation"
    },
    {
      "date": "2025-01-20T10:00:00Z",
      "event": "Vaccination Schedule Started",
      "details": "Initiated comprehensive vaccination program including FMD, BVD, and IBR vaccines"
    },
    {
      "date": "2025-02-01T14:30:00Z",
      "event": "Pregnancy Confirmation",
      "details": "Ultrasound confirmed pregnancy at 45 days, due date estimated for October 2025"
    },
    {
      "date": "2025-03-15T11:20:00Z",
      "event": "Nutritional Assessment",
      "details": "Dietary evaluation completed, mineral deficiency identified, supplementation started"
    },
    {
      "date": "2025-05-10T16:45:00Z",
      "event": "Lameness Issue",
      "details": "Mild lameness observed in left hind leg, hoof trimming and treatment administered"
    },
    {
      "date": "2025-05-15T09:30:00Z",
      "event": "Lameness Resolution",
      "details": "Full recovery from lameness, normal gait restored, preventive hoof care implemented"
    },
    {
      "date": "2025-07-20T13:10:00Z",
      "event": "Pregnancy Progress Check",
      "details": "Mid-pregnancy examination shows healthy fetus development, mother in excellent condition"
    },
    {
      "date": "2025-09-14T10:00:00Z",
      "event": "Pre-Calving Preparation",
      "details": "Moved to maternity pen, pre-calving vaccinations completed, ready for delivery"
    }
  ],
  
  "prescriptions": [
    {
      "prescriptionId": "PRESC_MED_001",
      "doctorName": "Dr. Emily Rodriguez",
      "date": "2025-03-15T11:20:00Z",
      "medicines": [
        {
          "name": "Calcium Supplement",
          "dosage": "100g",
          "duration": "60 days",
          "frequency": "once daily with feed"
        },
        {
          "name": "Phosphorus Supplement",
          "dosage": "50g",
          "duration": "60 days",
          "frequency": "once daily with feed"
        }
      ]
    },
    {
      "prescriptionId": "PRESC_MED_002",
      "doctorName": "Dr. James Wilson",
      "date": "2025-05-10T16:45:00Z",
      "medicines": [
        {
          "name": "Topical Antibiotic",
          "dosage": "Apply liberally",
          "duration": "7 days",
          "frequency": "twice daily to affected hoof"
        },
        {
          "name": "Anti-inflammatory",
          "dosage": "5mg/kg",
          "duration": "5 days",
          "frequency": "once daily"
        }
      ]
    }
  ],
  
  "treatments": [
    {
      "treatmentId": "TREAT_MED_001",
      "type": "Nutritional Deficiency Treatment",
      "startDate": "2025-03-15T11:20:00Z",
      "endDate": "2025-05-15T11:20:00Z",
      "status": "Completed",
      "medication": "Calcium + Phosphorus Supplements",
      "notes": "Successfully addressed mineral deficiency, improved overall health markers"
    },
    {
      "treatmentId": "TREAT_MED_002",
      "type": "Lameness Treatment",
      "startDate": "2025-05-10T16:45:00Z", 
      "endDate": "2025-05-20T16:45:00Z",
      "status": "Completed",
      "medication": "Topical Antibiotic + Anti-inflammatory",
      "notes": "Hoof infection treated successfully, implemented preventive hoof care routine"
    }
  ]
}
```

## 📋 Field Validation Rules

### Required Fields:
- `tagNo`: String (unique identifier)
- `breed`: String (animal breed)
- `gender`: String ("Male" or "Female")
- `farmId`: String (farm identifier)

### Date Format:
- Use ISO 8601 format: `"2025-09-14T10:30:00Z"`
- Or simple date: `"2025-09-14"`

### History Entry Structure:
```json
{
  "date": "ISO date string",
  "event": "Event name/type",
  "details": "Detailed description of what happened"
}
```

### Prescription Structure:
```json
{
  "prescriptionId": "Optional unique ID",
  "doctorName": "Prescribing veterinarian name",
  "date": "Prescription date",
  "medicines": [
    {
      "name": "Medicine name",
      "dosage": "Dosage amount",
      "duration": "Treatment duration",
      "frequency": "How often to administer"
    }
  ]
}
```

These payloads will work perfectly with your API and provide comprehensive animal records! 🚀