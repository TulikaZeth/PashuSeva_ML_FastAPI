#!/usr/bin/env python3
"""
Test script to verify dummy data implementation for AMU tracking
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'pashuseva_rag_bot', 'backend'))

from agents.amu_tracking_agent import AMUTrackingAgent

async def test_dummy_data():
    """Test the dummy data functionality"""
    print("Testing AMU Tracking Agent with dummy data...")
    
    # Initialize the agent
    amu_agent = AMUTrackingAgent()
    
    # Test case 1: Prescription with no medications
    print("\n=== Test Case 1: No medications ===")
    prescription_data_no_meds = {
        "animal_id": "A001",
        "date": datetime.now().isoformat(),
        "veterinarian": "Dr. Smith",
        "medications": []  # Empty medications list
    }
    
    result1 = await amu_agent.analyze_prescription_usage(prescription_data_no_meds)
    print(f"Status: {result1['status']}")
    print(f"Total medications: {result1['overall_assessment']['total_medications']}")
    print(f"Dummy data used: {result1['overall_assessment']['dummy_data_used']}")
    print(f"Medication analyses count: {len(result1['medication_analyses'])}")
    
    # Test case 2: Prescription with missing medications key
    print("\n=== Test Case 2: Missing medications key ===")
    prescription_data_missing = {
        "animal_id": "A002", 
        "date": datetime.now().isoformat(),
        "veterinarian": "Dr. Jones"
        # No medications key at all
    }
    
    result2 = await amu_agent.analyze_prescription_usage(prescription_data_missing)
    print(f"Status: {result2['status']}")
    print(f"Total medications: {result2['overall_assessment']['total_medications']}")
    print(f"Dummy data used: {result2['overall_assessment']['dummy_data_used']}")
    print(f"Medication analyses count: {len(result2['medication_analyses'])}")
    
    # Test case 3: Prescription with real medications (should not use dummy data)
    print("\n=== Test Case 3: Real medications ===")
    prescription_data_real = {
        "animal_id": "A003",
        "date": datetime.now().isoformat(),
        "veterinarian": "Dr. Brown",
        "medications": [
            {
                "drug_name": "Penicillin",
                "normalized_name": "penicillin",
                "dosage": "15 mg/kg",
                "frequency": "2 times per day",
                "duration": "3 days",
                "route": "injection"
            }
        ]
    }
    
    result3 = await amu_agent.analyze_prescription_usage(prescription_data_real)
    print(f"Status: {result3['status']}")
    print(f"Total medications: {result3['overall_assessment']['total_medications']}")
    print(f"Dummy data used: {result3['overall_assessment']['dummy_data_used']}")
    print(f"Medication analyses count: {len(result3['medication_analyses'])}")
    
    print("\n=== Test Results Summary ===")
    print("✓ Test 1 (empty medications): PASSED" if result1['status'] == 'success' and result1['overall_assessment']['dummy_data_used'] else "✗ Test 1: FAILED")
    print("✓ Test 2 (missing medications): PASSED" if result2['status'] == 'success' and result2['overall_assessment']['dummy_data_used'] else "✗ Test 2: FAILED")
    print("✓ Test 3 (real medications): PASSED" if result3['status'] == 'success' and not result3['overall_assessment']['dummy_data_used'] else "✗ Test 3: FAILED")
    
    return all([
        result1['status'] == 'success' and result1['overall_assessment']['dummy_data_used'],
        result2['status'] == 'success' and result2['overall_assessment']['dummy_data_used'],
        result3['status'] == 'success' and not result3['overall_assessment']['dummy_data_used']
    ])

if __name__ == "__main__":
    success = asyncio.run(test_dummy_data())
    if success:
        print("\n🎉 All tests passed! Dummy data implementation is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
