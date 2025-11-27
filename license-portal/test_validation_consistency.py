#!/usr/bin/env python3
"""
Test License Validation Consistency
Tests that a newly generated license validates consistently
"""

import sys
import time
import requests
import json

API_URL = "http://localhost:8000/api"

def test_license_validation_consistency():
    """Test that license validation is consistent"""
    print("=" * 60)
    print("License Validation Consistency Test")
    print("=" * 60)
    print()
    
    # Step 1: Generate a license
    print("1. Generating new license...")
    try:
        response = requests.post(
            f"{API_URL}/license/generate",
            json={
                "email": "test@example.com",
                "deployment_id": "test-consistency-123",
                "license_type": "trial"
            }
        )
        response.raise_for_status()
        license_data = response.json()
        license_key = license_data['license_key']
        print(f"✓ License generated successfully")
        print(f"  Type: {license_data['license_type']}")
        print(f"  Days: {license_data['days_valid']}")
        print(f"  Issue: {license_data['issue_date']}")
        print(f"  Expiry: {license_data['expiry_date']}")
        print()
    except Exception as e:
        print(f"✗ Failed to generate license: {e}")
        return False
    
    # Step 2: Validate immediately (should always be valid)
    print("2. Validating immediately after generation...")
    try:
        response = requests.post(
            f"{API_URL}/license/validate",
            json={"license_key": license_key}
        )
        response.raise_for_status()
        validation = response.json()
        
        if validation['valid']:
            print(f"✓ License is VALID")
            print(f"  Days remaining: {validation['days_remaining']}")
            print(f"  Expired: {validation['expired']}")
        else:
            print(f"✗ License is INVALID (ERROR!)")
            print(f"  Error: {validation.get('error')}")
            print(f"  Expired: {validation['expired']}")
            return False
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False
    
    print()
    
    # Step 3: Validate multiple times in quick succession
    print("3. Testing consistency (10 validations in 5 seconds)...")
    valid_count = 0
    invalid_count = 0
    
    for i in range(10):
        try:
            response = requests.post(
                f"{API_URL}/license/validate",
                json={"license_key": license_key}
            )
            response.raise_for_status()
            validation = response.json()
            
            if validation['valid']:
                valid_count += 1
                status = "✓ VALID"
            else:
                invalid_count += 1
                status = "✗ INVALID"
            
            print(f"  Attempt {i+1}: {status} (days: {validation['days_remaining']}, expired: {validation['expired']})")
            
            if i < 9:  # Don't sleep after last iteration
                time.sleep(0.5)
                
        except Exception as e:
            print(f"  Attempt {i+1}: ✗ ERROR - {e}")
            invalid_count += 1
    
    print()
    print("=" * 60)
    print("Results:")
    print("=" * 60)
    print(f"Valid validations:   {valid_count}/10")
    print(f"Invalid validations: {invalid_count}/10")
    print()
    
    if invalid_count == 0:
        print("✓ SUCCESS: All validations were consistent!")
        return True
    else:
        print("✗ FAILURE: Inconsistent validation results detected!")
        print()
        print("This indicates a timing or date comparison issue.")
        print("The license key is valid but validation is toggling.")
        return False

if __name__ == "__main__":
    success = test_license_validation_consistency()
    sys.exit(0 if success else 1)
