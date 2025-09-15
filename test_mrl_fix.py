#!/usr/bin/env python3
"""
Test script to verify MRL agent method calls work correctly
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'pashuseva_rag_bot', 'backend'))

from agents.mrl_compliance_agent import MRLComplianceAgent

async def test_mrl_methods():
    """Test the MRL agent method calls"""
    print("Testing MRL Agent Method Calls...")
    
    # Initialize MRL agent
    mrl_agent = MRLComplianceAgent()
    
    # Test parameters
    drug_name = "amoxicillin"
    species = "cattle"
    dosage = 20.0
    treatment_duration = 5
    days_since_treatment = 0
    body_weight = 500.0
    target_tissue = "muscle"
    
    try:
        # Test 1: predict_residue_levels method
        print("\n=== Test 1: predict_residue_levels ===")
        predicted_residues = mrl_agent.predict_residue_levels(
            drug_name, species, dosage, treatment_duration, days_since_treatment, body_weight
        )
        print(f"✅ predict_residue_levels successful")
        print(f"   - Muscle: {predicted_residues.get('muscle', 0):.4f} mg/kg")
        print(f"   - Liver: {predicted_residues.get('liver', 0):.4f} mg/kg")
        print(f"   - Kidney: {predicted_residues.get('kidney', 0):.4f} mg/kg")
        
    except Exception as e:
        print(f"❌ predict_residue_levels failed: {e}")
        return False
    
    try:
        # Test 2: check_mrl_compliance method
        print("\n=== Test 2: check_mrl_compliance ===")
        compliance_result = mrl_agent.check_mrl_compliance(drug_name, species, predicted_residues)
        print(f"✅ check_mrl_compliance successful")
        print(f"   - Status: {compliance_result.compliance_status}")
        print(f"   - Predicted level: {compliance_result.predicted_residue_level:.4f} mg/kg")
        print(f"   - MRL limit: {compliance_result.mrl_limit:.4f} mg/kg")
        print(f"   - Safety margin: {compliance_result.safety_margin:.1f}%")
        
    except Exception as e:
        print(f"❌ check_mrl_compliance failed: {e}")
        return False
    
    try:
        # Test 3: calculate_optimal_withdrawal_period method
        print("\n=== Test 3: calculate_optimal_withdrawal_period ===")
        withdrawal_recommendation = mrl_agent.calculate_optimal_withdrawal_period(
            drug_name, species, dosage, treatment_duration, body_weight, target_tissue
        )
        print(f"✅ calculate_optimal_withdrawal_period successful")
        print(f"   - Recommended days: {withdrawal_recommendation.get('recommended_days', 0)}")
        print(f"   - Standard days: {withdrawal_recommendation.get('standard_withdrawal_days', 0)}")
        print(f"   - Safety buffer: {withdrawal_recommendation.get('safety_buffer_days', 0)} days")
        
    except Exception as e:
        print(f"❌ calculate_optimal_withdrawal_period failed: {e}")
        return False
    
    try:
        # Test 4: generate_safety_alerts method
        print("\n=== Test 4: generate_safety_alerts ===")
        compliance_result.animal_id = "A001"
        safety_alerts = mrl_agent.generate_safety_alerts(compliance_result)
        print(f"✅ generate_safety_alerts successful")
        print(f"   - Alerts generated: {len(safety_alerts)}")
        for alert in safety_alerts:
            print(f"   - {alert.get('level', 'info').upper()}: {alert.get('title', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ generate_safety_alerts failed: {e}")
        return False
    
    print(f"\n=== Test Results Summary ===")
    print("✅ All MRL agent method calls successful!")
    print("✅ Method signatures are correct")
    print("✅ No argument count errors")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mrl_methods())
    if success:
        print("\n🎉 MRL agent method calls test completed successfully!")
    else:
        print("\n❌ Some method calls failed. Please check the implementation.")
        sys.exit(1)
