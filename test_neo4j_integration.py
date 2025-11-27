#!/usr/bin/env python3
"""
Test Neo4j Integration
Quick test script to verify Neo4j endpoints are working
"""
import requests
import json

BASE_URL = "http://localhost:8088/api/v1"

def test_get_settings():
    """Test getting all settings"""
    print("\n1. Testing GET /settings/all...")
    try:
        response = requests.get(f"{BASE_URL}/settings/all")
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            print("✅ Settings retrieved successfully")
            if 'neo4j' in data.get('settings', {}):
                print("✅ Neo4j settings found in response")
                print(f"   Neo4j config: {json.dumps(data['settings']['neo4j'], indent=2)}")
            else:
                print("❌ Neo4j settings NOT found in response")
        else:
            print(f"❌ Failed: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_neo4j_status():
    """Test Neo4j status endpoint"""
    print("\n2. Testing GET /settings/neo4j/status...")
    try:
        response = requests.get(f"{BASE_URL}/settings/neo4j/status")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        if data.get('enabled'):
            print("✅ Neo4j is enabled")
        else:
            print("⚠️  Neo4j is disabled")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_update_neo4j_settings():
    """Test updating Neo4j settings"""
    print("\n3. Testing PUT /settings/update (neo4j)...")
    payload = {
        "section": "neo4j",
        "settings": {
            "enabled": True,
            "uri": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "password",
            "database": "neo4j",
            "auto_sync": True,
            "max_relationship_depth": 2,
            "include_in_context": True
        }
    }
    try:
        response = requests.put(
            f"{BASE_URL}/settings/update",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")  # First 500 chars
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Settings updated successfully")
            else:
                print(f"❌ Update failed: {data}")
        else:
            print(f"❌ HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_neo4j_connection():
    """Test Neo4j connection"""
    print("\n4. Testing POST /settings/neo4j/test...")
    payload = {
        "uri": "bolt://localhost:7687",
        "username": "neo4j",
        "password": "password",
        "database": "neo4j"
    }
    try:
        response = requests.post(
            f"{BASE_URL}/settings/neo4j/test",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        if data.get('success'):
            print("✅ Connection test successful")
        else:
            print(f"⚠️  Connection test result: {data.get('message')}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Neo4j Integration Test Suite")
    print("=" * 60)
    
    test_get_settings()
    test_neo4j_status()
    test_update_neo4j_settings()
    test_neo4j_connection()
    
    print("\n" + "=" * 60)
    print("Test suite complete!")
    print("=" * 60)
