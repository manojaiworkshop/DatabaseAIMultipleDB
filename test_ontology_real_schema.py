#!/usr/bin/env python3
"""
Test ontology generation with your actual network management database
"""

# Sample schema from your database
sample_schema_summary = """DATABASE SCHEMA SUMMARY:
Total tables: 5

Table: device_status
  Columns (5):
    - status_id (integer) [PK, NOT NULL]
    - status_name (text) [NOT NULL]
    - status_description (text)
    - severity_level (integer)
    - created_at (timestamp)

Table: hardware_info
  Columns (9):
    - hardware_id (integer) [PK, NOT NULL]
    - hardware_type (text) [NOT NULL]
    - manufacturer (text)
    - model_number (text)
    - purchase_date (date)
    - warranty_years (integer)
    - unit_price (numeric)
    - supplier (text)
    - created_at (timestamp)

Table: maintenance_logs
  Columns (12):
    - log_id (integer) [PK, NOT NULL]
    - device_id (integer) [FK→network_devices]
    - maintenance_type (text)
    - description (text)
    - performed_by (text)
    - start_time (timestamp)
    - end_time (timestamp)
    - status (text)
    - notes (text)
    - cost (numeric)
    - next_maintenance (date)
    - created_at (timestamp)

Table: network_alerts
  Columns (13):
    - alert_id (integer) [PK, NOT NULL]
    - device_id (integer) [FK→network_devices]
    - alert_type (text)
    - severity (text)
    - message (text)
    - alert_time (timestamp)
    - acknowledged (boolean)
    - acknowledged_by (text)
    - acknowledged_time (timestamp)
    - resolved (boolean)
    - resolved_by (text)
    - resolved_time (timestamp)
    - created_at (timestamp)

Table: network_devices
  Columns (15):
    - device_id (integer) [PK, NOT NULL]
    - device_name (text) [NOT NULL]
    - device_type (text)
    - ip_address (inet)
    - mac_address (macaddr)
    - location (text)
    - status_id (integer) [FK→device_status]
    - hardware_id (integer) [FK→hardware_info]
    - firmware_version (text)
    - last_seen (timestamp)
    - uptime (interval)
    - cpu_usage (numeric)
    - memory_usage (numeric)
    - bandwidth_usage (bigint)
    - created_at (timestamp)
"""

expected_concepts = [
    "NetworkDevice",
    "DeviceStatus", 
    "HardwareInfo",
    "MaintenanceLog",
    "NetworkAlert"
]

expected_relationships = [
    ("NetworkDevice", "DeviceStatus", "has_status"),
    ("NetworkDevice", "HardwareInfo", "uses_hardware"),
    ("MaintenanceLog", "NetworkDevice", "maintains"),
    ("NetworkAlert", "NetworkDevice", "monitors"),
]

def test_schema_content():
    """Verify the schema contains actual tables"""
    print("="*60)
    print("TEST: Schema Content Validation")
    print("="*60)
    
    # Check for actual table names
    actual_tables = [
        "device_status",
        "hardware_info", 
        "maintenance_logs",
        "network_alerts",
        "network_devices"
    ]
    
    for table in actual_tables:
        if table in sample_schema_summary:
            print(f"✅ Found table: {table}")
        else:
            print(f"❌ Missing table: {table}")
            return False
    
    # Check that fake tables are NOT present
    fake_tables = ["customers", "orders", "products", "departments", "employees"]
    for table in fake_tables:
        if table.lower() in sample_schema_summary.lower():
            print(f"❌ Should NOT contain: {table}")
            return False
    
    print("\n✅ Schema contains correct tables")
    return True


def test_expected_concepts():
    """What concepts should be generated"""
    print("\n" + "="*60)
    print("EXPECTED CONCEPTS (Based on Your Schema)")
    print("="*60)
    
    for i, concept in enumerate(expected_concepts, 1):
        print(f"{i}. {concept}")
        print(f"   Tables: {concept.lower().replace('networkdevice', 'network_devices').replace('devicestatus', 'device_status').replace('hardwareinfo', 'hardware_info').replace('maintenancelog', 'maintenance_logs').replace('networkalert', 'network_alerts')}")
    
    print("\n" + "="*60)
    print("EXPECTED RELATIONSHIPS")
    print("="*60)
    
    for from_c, to_c, rel_type in expected_relationships:
        print(f"  {from_c} --[{rel_type}]--> {to_c}")
    
    return True


def test_wrong_concepts():
    """What should NOT be generated"""
    print("\n" + "="*60)
    print("SHOULD NOT GENERATE (Hallucinated Concepts)")
    print("="*60)
    
    wrong_concepts = [
        "Customer",
        "Order",
        "Product",
        "Department",
        "Employee",
        "Category",
        "Vendor",
        "Invoice"
    ]
    
    print("❌ These concepts do NOT exist in your database:")
    for concept in wrong_concepts:
        print(f"   - {concept}")
    
    print("\n⚠️  If ontology file contains these, the LLM is hallucinating!")
    return True


def main():
    print("\n" + "🧪"*30)
    print("ONTOLOGY GENERATION - REAL SCHEMA TEST")
    print("🧪"*30 + "\n")
    
    # Run tests
    test_schema_content()
    test_expected_concepts()
    test_wrong_concepts()
    
    print("\n" + "="*60)
    print("HOW TO VERIFY YOUR ONTOLOGY FILE")
    print("="*60)
    print("""
1. Look at the generated YAML file (ontology/*.yml)
2. Check the "concepts:" section
3. Verify:
   ✅ Concepts match actual tables (device_status, hardware_info, etc.)
   ❌ NO generic concepts (Customer, Order, Product, etc.)

4. Check "relationships:" section
5. Verify:
   ✅ Relationships use actual tables (network_devices → device_status)
   ❌ NO fake relationships (Order → Product)

If you see Customer/Order/Product concepts:
→ The LLM is ignoring your schema and hallucinating
→ The fixes in this PR should prevent that
""")
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("""
1. Restart backend: python run_backend.py
2. Connect to your database (192.168.1.2:5432/testing)
3. Click "Generate Ontology" in Settings
4. Check the generated YAML file
5. Verify concepts match the expected list above

If still getting wrong concepts, check backend logs for:
- "Raw structured response:" (see what LLM returns)
- "LLM returned X concepts" (should be ~5, not 6)
""")


if __name__ == "__main__":
    main()
