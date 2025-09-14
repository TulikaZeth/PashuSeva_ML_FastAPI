#!/usr/bin/env python3
"""
Test animal creation to debug 422 errors
"""
import requests
import json

# Test data that should work
test_animal = {
    "tagNo": "TEST123456",
    "breed": "Holstein",
    "gender": "Male",
    "farmId": "FARM001",
    "dateOfAdmission": "2025-09-14",
    "insurance": True,
    "vaccination": True,
    "summary": "Test animal for debugging"
}

# Additional test with minimal required fields only
minimal_animal = {
    "tagNo": "MINIMAL123",
    "breed": "Jersey",
    "gender": "Female", 
    "farmId": "FARM002"
}

def test_animal_creation():
    base_url = "http://localhost:8001"
    
    print("🧪 Testing Animal Creation")
    print("=" * 50)
    
    # Test 1: Full animal data
    print("\n📋 Test 1: Full Animal Data")
    print(f"Data: {json.dumps(test_animal, indent=2)}")
    
    try:
        response = requests.post(f"{base_url}/database/animals", json=test_animal)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:
            print("❌ Validation Error Details:")
            try:
                error_detail = response.json()
                print(json.dumps(error_detail, indent=2))
            except:
                print("Could not parse error response")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 2: Minimal animal data
    print("\n📋 Test 2: Minimal Animal Data")
    print(f"Data: {json.dumps(minimal_animal, indent=2)}")
    
    try:
        response = requests.post(f"{base_url}/database/animals", json=minimal_animal)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 422:
            print("❌ Validation Error Details:")
            try:
                error_detail = response.json()
                print(json.dumps(error_detail, indent=2))
            except:
                print("Could not parse error response")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_animal_creation()