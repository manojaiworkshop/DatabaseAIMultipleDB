#!/usr/bin/env python3
"""
Test License Integration between DatabaseAI and License Portal
"""
import requests
import json

print("=" * 60)
print("Testing License Portal Integration")
print("=" * 60)

# Test 1: Check License Portal API
print("\n1. Testing License Portal API (port 9999)...")
try:
    response = requests.get("http://localhost:9999/api/health", timeout=5)
    if response.status_code == 200:
        print("   ✓ License Portal API is running")
        print(f"   Response: {response.json()}")
    else:
        print(f"   ✗ License Portal API returned status {response.status_code}")
except Exception as e:
    print(f"   ✗ License Portal API is NOT accessible: {e}")

# Test 2: Check License Portal UI
print("\n2. Testing License Portal UI (port 9999)...")
try:
    response = requests.get("http://localhost:9999", timeout=5)
    if response.status_code == 200:
        print("   ✓ License Portal UI is accessible")
    else:
        print(f"   ✗ License Portal UI returned status {response.status_code}")
except Exception as e:
    print(f"   ✗ License Portal UI is NOT accessible: {e}")

# Test 3: Generate a test license
print("\n3. Generating a test license...")
try:
    test_data = {
        "email": "test@example.com",
        "deployment_id": "test-deployment-12345",
        "license_type": "trial"
    }
    response = requests.post(
        "http://localhost:9999/api/license/generate",
        json=test_data,
        timeout=5
    )
    if response.status_code == 200:
        license_data = response.json()
        print("   ✓ License generated successfully")
        print(f"   License Type: {license_data['license_type']}")
        print(f"   Days Valid: {license_data['days_valid']}")
        license_key = license_data['license_key']
        print(f"   License Key: {license_key[:50]}...")
        
        # Test 4: Validate the license
        print("\n4. Validating the generated license...")
        validate_response = requests.post(
            "http://localhost:9999/api/license/validate",
            json={"license_key": license_key},
            timeout=5
        )
        if validate_response.status_code == 200:
            validation = validate_response.json()
            print(f"   ✓ License is VALID: {validation['valid']}")
            print(f"   Deployment ID: {validation['deployment_id']}")
            print(f"   License Type: {validation['license_type']}")
            print(f"   Days Remaining: {validation['days_remaining']}")
            print(f"   Expired: {validation['expired']}")
        else:
            print(f"   ✗ Validation failed: {validate_response.status_code}")
            print(f"   Response: {validate_response.text}")
            
    else:
        print(f"   ✗ License generation failed: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ✗ License generation failed: {e}")

# Test 5: Check DatabaseAI backend
print("\n5. Testing DatabaseAI Backend (port 80)...")
try:
    response = requests.get("http://localhost:80/api/license/server-config", timeout=5)
    if response.status_code == 200:
        config = response.json()
        print("   ✓ DatabaseAI backend is running")
        print(f"   License Server URL: {config.get('server_url', 'Not configured')}")
    else:
        print(f"   ✗ DatabaseAI backend returned status {response.status_code}")
except Exception as e:
    print(f"   ✗ DatabaseAI backend is NOT accessible: {e}")

print("\n" + "=" * 60)
print("Summary:")
print("=" * 60)
print("\nTo activate a license in DatabaseAI:")
print("1. Open http://localhost:9999 (License Portal)")
print("2. Generate a new license with your email")
print("3. Copy the license key")
print("4. Open http://localhost (DatabaseAI)")
print("5. Go to Settings → License Settings")
print("6. Paste the license key and click 'Activate License'")
print("\nThe license should then be validated and stored in app_config.yml")
print("=" * 60)
