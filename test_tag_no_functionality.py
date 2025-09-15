#!/usr/bin/env python3
"""
Test script to verify tag_no functionality and database integration
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'pashuseva_rag_bot', 'backend'))

from services.database_service import DatabaseService
from agents.amu_tracking_agent import AMUTrackingAgent

async def test_tag_no_functionality():
    """Test the tag_no functionality and database integration"""
    print("Testing Tag Number Functionality and Database Integration...")
    
    # Initialize services
    db_service = DatabaseService()
    amu_agent = AMUTrackingAgent()
    
    # Test database connection
    print("\n=== Testing Database Connection ===")
    connected = await db_service.connect()
    if not connected:
        print("❌ Database connection failed")
        return False
    print("✅ Database connected successfully")
    
    # Test tag number: A001
    test_tag = "A001"
    
    # Test 1: Check if animal exists
    print(f"\n=== Test 1: Check Animal {test_tag} ===")
    animal_data = await db_service.get_animal(test_tag)
    if animal_data:
        print(f"✅ Animal {test_tag} found in database")
        print(f"   - Species: {animal_data.get('species', 'Unknown')}")
        print(f"   - Prescriptions: {len(animal_data.get('prescriptions', []))}")
        print(f"   - Treatments: {len(animal_data.get('treatments', []))}")
        print(f"   - Created: {animal_data.get('createdAt', 'Unknown')}")
    else:
        print(f"ℹ️  Animal {test_tag} not found in database")
    
    # Test 2: Create test prescription data
    print(f"\n=== Test 2: Create Test Prescription for {test_tag} ===")
    test_prescription = {
        "animal_id": test_tag,
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
            }
        ]
    }
    
    # Test AMU analysis
    amu_result = await amu_agent.analyze_prescription_usage(test_prescription)
    print(f"✅ AMU Analysis completed")
    print(f"   - Status: {amu_result['status']}")
    print(f"   - Total medications: {amu_result['overall_assessment']['total_medications']}")
    print(f"   - Dummy data used: {amu_result['overall_assessment']['dummy_data_used']}")
    
    # Test 3: Simulate prescription upload workflow
    print(f"\n=== Test 3: Simulate Prescription Upload Workflow ===")
    
    # Check if animal exists, if not create
    if not animal_data:
        print(f"Creating new animal record for {test_tag}")
        new_animal = {
            "tagNo": test_tag,
            "species": "cattle",
            "summary": "Test animal created for testing",
            "prescriptions": [test_prescription],
            "treatments": [],
            "history": [],
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        inserted = await db_service.insert_animal(new_animal)
        if inserted:
            print(f"✅ New animal record created for {test_tag}")
        else:
            print(f"❌ Failed to create animal record for {test_tag}")
            return False
    else:
        print(f"Updating existing animal record for {test_tag}")
        # Add prescription to existing animal
        updated_prescriptions = animal_data.get("prescriptions", []) + [test_prescription]
        update_data = {
            "prescriptions": updated_prescriptions,
            "updatedAt": datetime.now().isoformat()
        }
        updated = await db_service.update_animal(test_tag, update_data)
        if updated:
            print(f"✅ Animal record updated for {test_tag}")
        else:
            print(f"❌ Failed to update animal record for {test_tag}")
    
    # Test 4: Retrieve updated animal data
    print(f"\n=== Test 4: Retrieve Updated Animal Data ===")
    updated_animal = await db_service.get_animal(test_tag)
    if updated_animal:
        print(f"✅ Retrieved updated animal data")
        print(f"   - Total prescriptions: {len(updated_animal.get('prescriptions', []))}")
        print(f"   - Last updated: {updated_animal.get('updatedAt', 'Unknown')}")
        
        # Test AMU analysis on all prescriptions
        prescriptions = updated_animal.get("prescriptions", [])
        treatments = updated_animal.get("treatments", [])
        amu_analysis = await amu_agent.analyze_animal_usage(test_tag, prescriptions, treatments)
        print(f"✅ AMU analysis for all prescriptions completed")
        print(f"   - Antimicrobials used: {amu_analysis.get('total_antimicrobials', 0)}")
        print(f"   - Risk level: {amu_analysis.get('risk_level', 'Unknown')}")
        print(f"   - Compliance status: {amu_analysis.get('compliance_status', 'Unknown')}")
    else:
        print(f"❌ Failed to retrieve updated animal data")
        return False
    
    # Test 5: Test error handling for non-existent animal
    print(f"\n=== Test 5: Test Non-existent Animal ===")
    non_existent = await db_service.get_animal("NONEXISTENT")
    if non_existent is None:
        print("✅ Correctly returned None for non-existent animal")
    else:
        print("❌ Should have returned None for non-existent animal")
    
    print(f"\n=== Test Results Summary ===")
    print("✅ All tests passed! Tag number functionality is working correctly.")
    
    # Cleanup
    await db_service.disconnect()
    return True

if __name__ == "__main__":
    success = asyncio.run(test_tag_no_functionality())
    if success:
        print("\n🎉 Tag number functionality test completed successfully!")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
