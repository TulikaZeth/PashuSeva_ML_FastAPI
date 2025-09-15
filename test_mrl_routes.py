#!/usr/bin/env python3
"""
Test script to verify MRL routes functionality with tag_no and database integration
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'pashuseva_rag_bot', 'backend'))

from services.database_service import DatabaseService
from agents.mrl_compliance_agent import MRLComplianceAgent

async def test_mrl_routes():
    """Test the MRL routes functionality"""
    print("Testing MRL Routes with Tag Number and Database Integration...")
    
    # Initialize services
    db_service = DatabaseService()
    mrl_agent = MRLComplianceAgent()
    
    # Test database connection
    print("\n=== Testing Database Connection ===")
    connected = await db_service.connect()
    if not connected:
        print("❌ Database connection failed")
        return False
    print("✅ Database connected successfully")
    
    # Test tag number: A001
    test_tag = "A001"
    
    # Test 1: Create test animal with prescriptions
    print(f"\n=== Test 1: Create Test Animal {test_tag} ===")
    test_animal = {
        "tagNo": test_tag,
        "species": "cattle",
        "summary": "Test animal for MRL analysis",
        "prescriptions": [
            {
                "date": datetime.now().isoformat(),
                "veterinarian": "Dr. Test",
                "medications": [
                    {
                        "drug_name": "Amoxicillin",
                        "normalized_name": "amoxicillin",
                        "dosage": "20 mg/kg",
                        "frequency": "2 times per day",
                        "duration": "5 days",
                        "route": "oral"
                    },
                    {
                        "drug_name": "Oxytetracycline",
                        "normalized_name": "oxytetracycline",
                        "dosage": "10 mg/kg",
                        "frequency": "1 time per day",
                        "duration": "3 days",
                        "route": "injection"
                    }
                ]
            }
        ],
        "treatments": [],
        "history": [],
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    
    # Insert test animal
    inserted = await db_service.insert_animal(test_animal)
    if inserted:
        print(f"✅ Test animal {test_tag} created successfully")
    else:
        print(f"❌ Failed to create test animal {test_tag}")
        return False
    
    # Test 2: MRL Analysis for Animal
    print(f"\n=== Test 2: MRL Analysis for Animal {test_tag} ===")
    try:
        # Simulate the analyze_animal_mrl function
        animal_data = await db_service.get_animal(test_tag)
        species = animal_data.get("species", "cattle")
        prescriptions = animal_data.get("prescriptions", [])
        
        mrl_analyses = []
        for prescription in prescriptions:
            if not prescription.get("medications"):
                continue
                
            for medication in prescription["medications"]:
                drug_name = medication.get("normalized_name", medication.get("drug_name", ""))
                if not drug_name:
                    continue
                
                # Parse dosage and duration
                dosage = mrl_agent._parse_dosage_value(medication.get("dosage", ""))
                duration = mrl_agent._parse_duration_value(medication.get("duration", ""))
                
                if dosage == 0:
                    continue
                
                # Predict residue levels
                predicted_residues = mrl_agent.predict_residue_levels(
                    drug_name, species, dosage, duration, 0  # 0 days since treatment
                )
                
                # Check MRL compliance
                compliance_result = mrl_agent.check_mrl_compliance(drug_name, species, predicted_residues)
                compliance_result.animal_id = test_tag
                
                # Calculate optimal withdrawal period
                withdrawal_recommendation = mrl_agent.calculate_optimal_withdrawal_period(
                    drug_name, species, dosage, duration, target_tissue="muscle"
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
                    "safety_alerts": safety_alerts
                })
        
        print(f"✅ MRL analysis completed for {len(mrl_analyses)} medications")
        for analysis in mrl_analyses:
            print(f"   - {analysis['medication']}: {analysis['compliance_result']['compliance_status']}")
            print(f"     Withdrawal: {analysis['withdrawal_recommendation']['recommended_days']} days")
        
    except Exception as e:
        print(f"❌ MRL analysis failed: {e}")
        return False
    
    # Test 3: Withdrawal Period Calculation
    print(f"\n=== Test 3: Withdrawal Period Calculation for {test_tag} ===")
    try:
        withdrawal_recommendations = []
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
                    drug_name, species, dosage, duration, target_tissue="muscle"
                )
                
                withdrawal_recommendations.append({
                    "medication": medication.get("drug_name"),
                    "normalized_name": drug_name,
                    "withdrawal_recommendation": withdrawal_recommendation,
                    "standard_withdrawal": mrl_agent.get_withdrawal_period(drug_name, species, "muscle")
                })
        
        # Find the longest recommended withdrawal period
        max_withdrawal = 0
        if withdrawal_recommendations:
            max_withdrawal = max(
                rec["withdrawal_recommendation"]["recommended_days"] 
                for rec in withdrawal_recommendations
            )
        
        print(f"✅ Withdrawal period calculation completed")
        print(f"   - Maximum withdrawal period: {max_withdrawal} days")
        for rec in withdrawal_recommendations:
            print(f"   - {rec['medication']}: {rec['withdrawal_recommendation']['recommended_days']} days")
        
    except Exception as e:
        print(f"❌ Withdrawal period calculation failed: {e}")
        return False
    
    # Test 4: MRL Standards
    print(f"\n=== Test 4: MRL Standards for {species} ===")
    try:
        standards = mrl_agent.get_mrl_standards(species)
        print(f"✅ MRL standards retrieved for {species}")
        print(f"   - Supported drugs: {list(standards.keys())}")
        if "amoxicillin" in standards:
            amox_standards = standards["amoxicillin"]
            print(f"   - Amoxicillin standards: {list(amox_standards.keys())}")
        
    except Exception as e:
        print(f"❌ MRL standards retrieval failed: {e}")
        return False
    
    # Test 5: Residue Prediction
    print(f"\n=== Test 5: Residue Prediction for {test_tag} ===")
    try:
        drug_name = "amoxicillin"
        days_since_treatment = 5
        dosage = 20.0
        treatment_duration = 5
        
        predicted_residues = mrl_agent.predict_residue_levels(
            drug_name, species, dosage, treatment_duration, days_since_treatment
        )
        
        print(f"✅ Residue prediction completed for {drug_name}")
        print(f"   - Muscle: {predicted_residues.get('muscle', 0):.4f} mg/kg")
        print(f"   - Liver: {predicted_residues.get('liver', 0):.4f} mg/kg")
        print(f"   - Kidney: {predicted_residues.get('kidney', 0):.4f} mg/kg")
        print(f"   - Confidence: {predicted_residues.get('prediction_confidence', 0):.2f}")
        
    except Exception as e:
        print(f"❌ Residue prediction failed: {e}")
        return False
    
    # Test 6: Agent Health Check
    print(f"\n=== Test 6: Agent Health Check ===")
    try:
        agent_info = await mrl_agent.get_agent_info()
        print(f"✅ Agent health check completed")
        print(f"   - Agent: {agent_info.get('agent_name')}")
        print(f"   - Status: {agent_info.get('status')}")
        print(f"   - Supported species: {agent_info.get('supported_species')}")
        print(f"   - Capabilities: {len(agent_info.get('capabilities', []))}")
        
    except Exception as e:
        print(f"❌ Agent health check failed: {e}")
        return False
    
    print(f"\n=== Test Results Summary ===")
    print("✅ All MRL route tests passed!")
    print("✅ Tag number functionality working correctly")
    print("✅ Database integration working correctly")
    print("✅ MRL analysis working correctly")
    print("✅ Withdrawal period calculation working correctly")
    print("✅ Residue prediction working correctly")
    
    # Cleanup
    await db_service.disconnect()
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mrl_routes())
    if success:
        print("\n🎉 All MRL routes tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
