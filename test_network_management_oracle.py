#!/usr/bin/env python3
"""
Network Management Database Test Script for Oracle
Creates 5 interconnected tables with sample data for testing DatabaseAI with Oracle
"""

import oracledb
from datetime import datetime, timedelta
import random
import os

print("=" * 80)
print("NETWORK MANAGEMENT DATABASE SETUP - ORACLE")
print("=" * 80)

# Oracle Connection Configuration
ORACLE_CONFIG = {
    'user': os.environ.get('ORACLE_USER', 'pgaiview'),
    'password': os.environ.get('ORACLE_PASSWORD', 'pgaiview123'),
    'dsn': os.environ.get('ORACLE_DSN', 'localhost:1521/XE')
}

print(f"\n📋 Connection Configuration:")
print(f"   • User: {ORACLE_CONFIG['user']}")
print(f"   • DSN: {ORACLE_CONFIG['dsn']}")
print()

try:
    # Connect to Oracle
    print("🔌 Connecting to Oracle Database...")
    conn = oracledb.connect(
        user=ORACLE_CONFIG['user'],
        password=ORACLE_CONFIG['password'],
        dsn=ORACLE_CONFIG['dsn']
    )
    cursor = conn.cursor()
    print("   ✓ Connected successfully\n")

    # Drop existing tables if they exist
    print("1. Dropping existing tables (if any)...")
    drop_tables = [
        "DROP TABLE network_alerts CASCADE CONSTRAINTS",
        "DROP TABLE maintenance_logs CASCADE CONSTRAINTS",
        "DROP TABLE network_devices CASCADE CONSTRAINTS",
        "DROP TABLE device_status CASCADE CONSTRAINTS",
        "DROP TABLE hardware_info CASCADE CONSTRAINTS"
    ]

    for drop_query in drop_tables:
        try:
            cursor.execute(drop_query)
            print(f"   ✓ {drop_query}")
        except oracledb.DatabaseError as e:
            # Ignore table doesn't exist error
            if 'ORA-00942' not in str(e):
                print(f"   ⚠ {drop_query} - {e}")

    # Drop sequences
    print("\n   Dropping sequences...")
    drop_sequences = [
        "DROP SEQUENCE hardware_info_seq",
        "DROP SEQUENCE device_status_seq",
        "DROP SEQUENCE network_devices_seq",
        "DROP SEQUENCE maintenance_logs_seq",
        "DROP SEQUENCE network_alerts_seq"
    ]

    for drop_seq in drop_sequences:
        try:
            cursor.execute(drop_seq)
        except:
            pass

    # Create sequences for auto-increment
    print("\n2. Creating sequences...")
    sequences = [
        "CREATE SEQUENCE hardware_info_seq START WITH 1 INCREMENT BY 1",
        "CREATE SEQUENCE device_status_seq START WITH 1 INCREMENT BY 1",
        "CREATE SEQUENCE network_devices_seq START WITH 1 INCREMENT BY 1",
        "CREATE SEQUENCE maintenance_logs_seq START WITH 1 INCREMENT BY 1",
        "CREATE SEQUENCE network_alerts_seq START WITH 1 INCREMENT BY 1"
    ]

    for seq in sequences:
        cursor.execute(seq)
        print(f"   ✓ {seq}")

    # Create tables with relationships
    print("\n3. Creating tables...")

    # Table 1: hardware_info (Parent table)
    cursor.execute("""
    CREATE TABLE hardware_info (
        hardware_id NUMBER PRIMARY KEY,
        hardware_type VARCHAR2(50) NOT NULL,
        manufacturer VARCHAR2(100) NOT NULL,
        model_number VARCHAR2(100) NOT NULL,
        purchase_date DATE NOT NULL,
        warranty_years NUMBER DEFAULT 3,
        unit_price NUMBER(10, 2) NOT NULL,
        supplier VARCHAR2(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("   ✓ Created table: hardware_info")

    # Table 2: device_status (Reference table)
    cursor.execute("""
    CREATE TABLE device_status (
        status_id NUMBER PRIMARY KEY,
        status_name VARCHAR2(50) UNIQUE NOT NULL,
        status_description VARCHAR2(500),
        severity_level NUMBER CHECK (severity_level BETWEEN 1 AND 5),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("   ✓ Created table: device_status")

    # Table 3: network_devices (Main operational table with FKs)
    cursor.execute("""
    CREATE TABLE network_devices (
        device_id NUMBER PRIMARY KEY,
        device_name VARCHAR2(100) NOT NULL,
        hardware_id NUMBER REFERENCES hardware_info(hardware_id) ON DELETE CASCADE,
        status_id NUMBER REFERENCES device_status(status_id) ON DELETE SET NULL,
        ip_address VARCHAR2(45) UNIQUE NOT NULL,
        location VARCHAR2(200) NOT NULL,
        floor_number NUMBER,
        building VARCHAR2(100),
        installation_date DATE NOT NULL,
        last_maintenance_date DATE,
        uptime_hours NUMBER DEFAULT 0,
        cpu_usage_percent NUMBER(5, 2),
        memory_usage_percent NUMBER(5, 2),
        bandwidth_usage_mbps NUMBER(10, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("   ✓ Created table: network_devices")

    # Table 4: maintenance_logs (Historical records with FK to devices)
    cursor.execute("""
    CREATE TABLE maintenance_logs (
        log_id NUMBER PRIMARY KEY,
        device_id NUMBER REFERENCES network_devices(device_id) ON DELETE CASCADE,
        maintenance_type VARCHAR2(50) NOT NULL,
        performed_by VARCHAR2(100) NOT NULL,
        maintenance_date DATE NOT NULL,
        duration_hours NUMBER(4, 2),
        cost NUMBER(10, 2),
        description VARCHAR2(500),
        issues_found VARCHAR2(500),
        actions_taken VARCHAR2(500),
        next_maintenance_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("   ✓ Created table: maintenance_logs")

    # Table 5: network_alerts (Alert system with FK to devices)
    cursor.execute("""
    CREATE TABLE network_alerts (
        alert_id NUMBER PRIMARY KEY,
        device_id NUMBER REFERENCES network_devices(device_id) ON DELETE CASCADE,
        alert_type VARCHAR2(50) NOT NULL,
        severity VARCHAR2(20) CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
        alert_message VARCHAR2(500) NOT NULL,
        alert_timestamp TIMESTAMP NOT NULL,
        acknowledged NUMBER(1) DEFAULT 0,
        acknowledged_by VARCHAR2(100),
        acknowledged_at TIMESTAMP,
        resolved NUMBER(1) DEFAULT 0,
        resolved_at TIMESTAMP,
        resolution_notes VARCHAR2(500),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("   ✓ Created table: network_alerts")

    # Insert sample data
    print("\n4. Inserting sample data...")

    # Insert hardware_info (10 records)
    hardware_data = [
        ('Router', 'Cisco', 'ISR-4451', datetime(2022, 1, 15), 5, 2500.00, 'TechSupply Inc'),
        ('Switch', 'HP', 'Aruba-2930F', datetime(2022, 2, 20), 3, 800.00, 'NetGear Supply'),
        ('Firewall', 'Fortinet', 'FortiGate-100F', datetime(2021, 11, 10), 5, 3500.00, 'SecureNet'),
        ('Access Point', 'Ubiquiti', 'UAP-AC-PRO', datetime(2022, 3, 5), 2, 150.00, 'Wireless Solutions'),
        ('Server', 'Dell', 'PowerEdge-R740', datetime(2021, 8, 20), 5, 5000.00, 'Dell Direct'),
        ('Router', 'Juniper', 'MX204', datetime(2022, 5, 12), 5, 4200.00, 'TechSupply Inc'),
        ('Switch', 'Cisco', 'Catalyst-9300', datetime(2022, 6, 18), 3, 1200.00, 'NetGear Supply'),
        ('Firewall', 'Palo Alto', 'PA-220', datetime(2021, 12, 1), 5, 2800.00, 'SecureNet'),
        ('Access Point', 'Cisco', 'Meraki-MR46', datetime(2022, 7, 22), 3, 600.00, 'Wireless Solutions'),
        ('Server', 'HP', 'ProLiant-DL380', datetime(2021, 9, 15), 5, 4500.00, 'HP Enterprise')
    ]

    for hw in hardware_data:
        cursor.execute("""
            INSERT INTO hardware_info (hardware_id, hardware_type, manufacturer, model_number, purchase_date, 
                                       warranty_years, unit_price, supplier)
            VALUES (hardware_info_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7)
        """, hw)
    conn.commit()
    print(f"   ✓ Inserted {len(hardware_data)} records into hardware_info")

    # Insert device_status (5 statuses)
    status_data = [
        ('Online', 'Device is operational and responsive', 1),
        ('Offline', 'Device is not responding', 5),
        ('Maintenance', 'Device is undergoing scheduled maintenance', 2),
        ('Warning', 'Device has warning conditions', 3),
        ('Critical', 'Device has critical issues requiring immediate attention', 5)
    ]

    for status in status_data:
        cursor.execute("""
            INSERT INTO device_status (status_id, status_name, status_description, severity_level)
            VALUES (device_status_seq.NEXTVAL, :1, :2, :3)
        """, status)
    conn.commit()
    print(f"   ✓ Inserted {len(status_data)} records into device_status")

    # Insert network_devices (10 records)
    locations = [
        ('Main Router - Building A', 1, 'Building A'),
        ('Core Switch - Building A', 1, 'Building A'),
        ('Main Firewall - DMZ', 0, 'Data Center'),
        ('WiFi AP - Floor 2 East', 2, 'Building B'),
        ('Database Server - DC1', 0, 'Data Center'),
        ('Backup Router - Building B', 1, 'Building B'),
        ('Distribution Switch - Floor 3', 3, 'Building A'),
        ('Perimeter Firewall', 0, 'Data Center'),
        ('WiFi AP - Floor 4 West', 4, 'Building B'),
        ('Application Server - DC2', 0, 'Data Center')
    ]

    ip_base = "192.168"
    for i in range(10):
        hw_id = i + 1
        status_id = random.choice([1, 1, 1, 1, 4])  # Mostly online, some warnings
        ip = f"{ip_base}.{i+1}.{random.randint(10, 250)}"
        location, floor, building = locations[i]
        install_date = datetime.now() - timedelta(days=random.randint(365, 730))
        last_maint = datetime.now() - timedelta(days=random.randint(30, 180))
        uptime = random.randint(100, 10000)
        cpu = round(random.uniform(10.0, 85.0), 2)
        memory = round(random.uniform(20.0, 90.0), 2)
        bandwidth = round(random.uniform(50.0, 950.0), 2)
        
        cursor.execute("""
            INSERT INTO network_devices (device_id, device_name, hardware_id, status_id, ip_address, location,
                                         floor_number, building, installation_date, last_maintenance_date,
                                         uptime_hours, cpu_usage_percent, memory_usage_percent, bandwidth_usage_mbps)
            VALUES (network_devices_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13)
        """, (f"Device-{i+1:03d}", hw_id, status_id, ip, location, floor, building, 
              install_date, last_maint, uptime, cpu, memory, bandwidth))
    conn.commit()
    print(f"   ✓ Inserted 10 records into network_devices")

    # Insert maintenance_logs (15 records - multiple per device)
    maintenance_types = ['Routine Check', 'Hardware Upgrade', 'Software Update', 'Emergency Repair', 'Performance Tuning']
    technicians = ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Lisa Chen', 'Robert Brown']

    for i in range(15):
        device_id = random.randint(1, 10)
        maint_type = random.choice(maintenance_types)
        tech = random.choice(technicians)
        maint_date = datetime.now() - timedelta(days=random.randint(1, 365))
        duration = round(random.uniform(0.5, 8.0), 2)
        cost = round(random.uniform(50.0, 500.0), 2)
        next_maint = maint_date + timedelta(days=90)
        
        cursor.execute("""
            INSERT INTO maintenance_logs (log_id, device_id, maintenance_type, maintenance_date, 
                                         performed_by, duration_hours, cost, description, issues_found,
                                         actions_taken, next_maintenance_date)
            VALUES (maintenance_logs_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
        """, (device_id, maint_type, maint_date, tech, duration, cost,
              f'{maint_type} performed on device',
              'Minor wear and tear observed' if random.random() > 0.5 else 'No issues found',
              'Cleaned and tested all components',
              next_maint))
    conn.commit()
    print(f"   ✓ Inserted 15 records into maintenance_logs")

    # Insert network_alerts (20 records)
    alert_types = ['High CPU Usage', 'Memory Threshold', 'Connection Loss', 'Security Threat', 
                   'Bandwidth Spike', 'Hardware Failure', 'Temperature Alert', 'Power Fluctuation']
    severities = ['Low', 'Medium', 'High', 'Critical']

    for i in range(20):
        device_id = random.randint(1, 10)
        alert_type = random.choice(alert_types)
        severity = random.choice(severities)
        alert_time = datetime.now() - timedelta(hours=random.randint(1, 720))
        acknowledged = random.choice([1, 1, 0])  # 2/3 acknowledged
        resolved = acknowledged and random.choice([1, 0])
        
        ack_by = random.choice(technicians) if acknowledged else None
        ack_at = alert_time + timedelta(minutes=random.randint(5, 120)) if acknowledged else None
        resolved_at = ack_at + timedelta(minutes=random.randint(30, 480)) if resolved else None
        
        cursor.execute("""
            INSERT INTO network_alerts (alert_id, device_id, alert_type, severity, alert_message, alert_timestamp,
                                        acknowledged, acknowledged_by, acknowledged_at, resolved, resolved_at,
                                        resolution_notes)
            VALUES (network_alerts_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11)
        """, (device_id, alert_type, severity, 
              f'{alert_type} detected on device - requires attention',
              alert_time, acknowledged, ack_by, ack_at, resolved, resolved_at,
              'Issue resolved after investigation' if resolved else None))
    conn.commit()
    print(f"   ✓ Inserted 20 records into network_alerts")

    print("\n" + "=" * 80)
    print("DATABASE SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 80)

    # Display summary statistics
    print("\n5. Database Summary:")
    cursor.execute("SELECT COUNT(*) FROM hardware_info")
    print(f"   • Hardware Info: {cursor.fetchone()[0]} records")

    cursor.execute("SELECT COUNT(*) FROM device_status")
    print(f"   • Device Status: {cursor.fetchone()[0]} records")

    cursor.execute("SELECT COUNT(*) FROM network_devices")
    print(f"   • Network Devices: {cursor.fetchone()[0]} records")

    cursor.execute("SELECT COUNT(*) FROM maintenance_logs")
    print(f"   • Maintenance Logs: {cursor.fetchone()[0]} records")

    cursor.execute("SELECT COUNT(*) FROM network_alerts")
    print(f"   • Network Alerts: {cursor.fetchone()[0]} records")

    print("\n" + "=" * 80)
    print("COMPLEX TEST QUERIES FOR DatabaseAI - ORACLE")
    print("=" * 80)

    test_queries = [
        {
            "id": 1,
            "category": "Multi-table JOIN with Aggregation",
            "query": "Show me all network devices with their hardware information and total maintenance cost",
            "description": "Joins network_devices, hardware_info, and maintenance_logs"
        },
        {
            "id": 2,
            "category": "Subquery with Filtering",
            "query": "Which devices have had more than 2 critical alerts in the last month?",
            "description": "Subquery counting alerts with date filtering"
        },
        {
            "id": 3,
            "category": "Complex JOIN with Status",
            "query": "List all Cisco devices that are currently offline or in warning state with their last maintenance date",
            "description": "3-table JOIN with manufacturer and status filtering"
        },
        {
            "id": 4,
            "category": "Aggregation with GROUP BY",
            "query": "Show total maintenance cost per building and which technician spent the most time",
            "description": "Multiple aggregations grouped by location"
        },
        {
            "id": 5,
            "category": "Window Function",
            "query": "Rank devices by CPU usage and show the top 5 with their hardware type",
            "description": "Window function with JOIN"
        },
        {
            "id": 6,
            "category": "Date Calculation",
            "query": "Which devices need maintenance in the next 30 days based on their last maintenance date?",
            "description": "Date arithmetic with JOIN"
        },
        {
            "id": 7,
            "category": "Nested Aggregation",
            "query": "What's the average cost of maintenance per hardware manufacturer?",
            "description": "3-table JOIN with nested aggregation"
        },
        {
            "id": 8,
            "category": "Multiple Conditions",
            "query": "Show me all routers and firewalls in Building A with CPU usage above 70% that have unresolved critical alerts",
            "description": "4-table JOIN with multiple complex conditions"
        },
        {
            "id": 9,
            "category": "Time-based Analysis",
            "query": "Which technician resolved the most alerts in the last 6 months?",
            "description": "Aggregation with date range filtering"
        },
        {
            "id": 10,
            "category": "Complex VIEW Creation",
            "query": "Create a view showing device health status including hardware info, current alerts, and maintenance history",
            "description": "Multi-table VIEW with all 5 tables"
        },
        {
            "id": 11,
            "category": "Conditional Aggregation",
            "query": "Show devices with their total uptime, number of critical alerts, and whether they're under warranty",
            "description": "Multiple JOINs with CASE statements"
        },
        {
            "id": 12,
            "category": "Correlation Analysis",
            "query": "Find devices where high CPU usage correlates with multiple maintenance events",
            "description": "Subquery with correlation logic"
        },
        {
            "id": 13,
            "category": "Cost Analysis",
            "query": "What's the total cost of ownership for each device including purchase price and maintenance?",
            "description": "Complex calculation with JOINs and aggregation"
        },
        {
            "id": 14,
            "category": "Geographic Distribution",
            "query": "Show me the distribution of device types across all buildings with their average bandwidth usage",
            "description": "GROUP BY with multiple dimensions"
        },
        {
            "id": 15,
            "category": "Performance Bottleneck",
            "query": "Which devices have both high memory usage and low uptime hours indicating potential problems?",
            "description": "Multiple conditions with performance metrics"
        }
    ]

    print("\n📝 SAMPLE NLP QUERIES TO TEST:\n")
    for query in test_queries:
        print(f"{query['id']}. [{query['category']}]")
        print(f"   Query: \"{query['query']}\"")
        print(f"   Tests: {query['description']}\n")

    print("=" * 80)
    print("Copy any of the above queries into your DatabaseAI chat interface to test!")
    print("=" * 80)

    # Close connection
    cursor.close()
    conn.close()

    print("\n✅ Test database setup complete! You can now test DatabaseAI with Oracle queries.")

except oracledb.DatabaseError as e:
    error, = e.args
    print(f"\n❌ Database Error:")
    print(f"   Code: {error.code}")
    print(f"   Message: {error.message}")
    import traceback
    traceback.print_exc()

except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
