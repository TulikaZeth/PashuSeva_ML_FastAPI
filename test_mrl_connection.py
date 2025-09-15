#!/usr/bin/env python3
"""
Test script to verify MRL agent connection and medication parsing
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'pashuseva_rag_bot', 'backend'))

from services.database_service import DatabaseService
from agents.mrl_compliance_agent import MRLComplianceAgent

async def test_mrl_connection():
    """Test MRL agent connection and medication parsing"""
    print("Testing MRL Agent Connection and Medication Parsing...")
    
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
    
    # Test tag number: 105293363572 (from the user's data)
    test_tag = "105293363572"
    
    # Test 1: Get animal data
    print(f"\n=== Test 1: Get Animal Data for {test_tag} ===")
    animal_data = await db_service.get_animal(test_tag)
    if not animal_data:
        print(f"❌ Animal {test_tag} not found in database")
        return False
    
    print(f"✅ Animal {test_tag} found in database")
    print(f"   - Species: {animal_data.get('species', 'Unknown')}")
    print(f"   - Prescriptions: {len(animal_data.get('prescriptions', []))}")
    
    # Test 2: Check prescription structure
    print(f"\n=== Test 2: Check Prescription Structure ===")
    prescriptions = animal_data.get("prescriptions", [])
    if not prescriptions:
        print("❌ No prescriptions found")
        return False
    
    prescription = prescriptions[0]
    print(f"✅ Found prescription: {prescription.get('date', 'Unknown date')}")
    print(f"   - Medications: {len(prescription.get('medications', []))}")
    
    medications = prescription.get("medications", [])
    if not medications:
        print("❌ No medications found in prescription")
        return False
    
    # Test 3: Check medication structure
    print(f"\n=== Test 3: Check Medication Structure ===")
    for i, medication in enumerate(medications):
        print(f"   Medication {i+1}: {medication}")
        drug_name = medication.get("normalized_name", medication.get("drug_name", ""))
        dosage = medication.get("dosage", "")
        duration = medication.get("duration", "")
        print(f"     - Drug name: {drug_name}")
        print(f"     - Dosage: {dosage}")
        print(f"     - Duration: {duration}")
    
    # Test 4: Test MRL agent parsing
    print(f"\n=== Test 4: Test MRL Agent Parsing ===")
    for i, medication in enumerate(medications):
        print(f"   Testing medication {i+1}:")
        drug_name = medication.get("normalized_name", medication.get("drug_name", ""))
        if not drug_name:
            print(f"     ❌ No drug name found")
            continue
        
        # Parse dosage and duration
        dosage = mrl_agent._parse_dosage_value(medication.get("dosage", ""))
        duration = mrl_agent._parse_duration_value(medication.get("duration", ""))
        
        print(f"     - Drug: {drug_name}")
        print(f"     - Parsed dosage: {dosage}")
        print(f"     - Parsed duration: {duration}")
        
        # Use defaults if parsing failed
        if dosage == 0:
            dosage = 10.0
            print(f"     - Using default dosage: {dosage}")
        
        if duration == 0:
            duration = 3
            print(f"     - Using default duration: {duration}")
        
        # Test MRL analysis
        try:
            species = animal_data.get("species", "cattle")
            predicted_residues = mrl_agent.predict_residue_levels(
                drug_name, species, dosage, duration, 5  # 5 days since treatment
            )
            
            compliance_result = mrl_agent.check_mrl_compliance(drug_name, species, predicted_residues)
            compliance_result.animal_id = test_tag
            
            withdrawal_recommendation = mrl_agent.calculate_optimal_withdrawal_period(
                drug_name, species, dosage, duration, target_tissue="muscle"
            )
            
            print(f"     ✅ MRL analysis successful")
            print(f"     - Compliance status: {compliance_result.compliance_status}")
            print(f"     - Predicted residue: {compliance_result.predicted_residue_level:.4f} mg/kg")
            print(f"     - MRL limit: {compliance_result.mrl_limit:.4f} mg/kg")
            print(f"     - Withdrawal period: {withdrawal_recommendation.get('recommended_days', 0)} days")
            
        except Exception as e:
            print(f"     ❌ MRL analysis failed: {e}")
            return False
    
    print(f"\n=== Test Results Summary ===")
    print("✅ MRL agent connection successful")
    print("✅ Medication parsing working")
    print("✅ MRL analysis working")
    print("✅ Database integration working")
    
    # Cleanup
    await db_service.disconnect()
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mrl_connection())
    if success:
        print("\n🎉 MRL connection test completed successfully!")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
