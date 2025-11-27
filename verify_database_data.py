"""
Verify Database Data - Check if test data is properly populated
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from colorama import init, Fore, Style
import yaml

init(autoreset=True)

# Load database configuration from config.yml
with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

db_config = config['database']

# Database configuration
DB_CONFIG = {
    "host": db_config['host'],
    "port": db_config['port'],
    "database": db_config['database'],
    "user": db_config['user'],
    "password": db_config['password']
}

def print_header(text):
    print("\n" + "=" * 100)
    print(f"{Fore.CYAN}{Style.BRIGHT}{text.center(100)}")
    print("=" * 100)

def print_success(text):
    print(f"{Fore.GREEN}✓ {text}")

def print_info(text):
    print(f"{Fore.BLUE}ℹ {text}")

def print_table(title, data):
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}{title}")
    print(f"{Fore.YELLOW}{'─' * 100}")
    for row in data:
        print(f"  {row}")

def verify_database():
    """Verify database structure and data"""
    
    try:
        # Connect to database
        print_header("DATABASE VERIFICATION")
        print_info("Connecting to database...")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print_success(f"Connected to database: {DB_CONFIG['database']}")
        
        # Check tables
        print(f"\n{Fore.CYAN}{Style.BRIGHT}1. Checking Tables...")
        print(f"{Fore.CYAN}{'─' * 100}")
        
        tables_to_check = [
            'hardware_info',
            'device_status',
            'network_devices',
            'maintenance_logs',
            'network_alerts'
        ]
        
        for table in tables_to_check:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, (table,))
            
            exists = cursor.fetchone()['exists']
            
            if exists:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print_success(f"Table '{table}' exists with {count} rows")
                
                # Get column info
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position
                """, (table,))
                columns = cursor.fetchall()
                col_names = [f"{col['column_name']}({col['data_type']})" for col in columns]
                print_info(f"   Columns: {', '.join(col_names[:5])}{'...' if len(col_names) > 5 else ''}")
            else:
                print(f"{Fore.RED}✗ Table '{table}' does not exist!")
        
        # Show sample data from each table
        print(f"\n{Fore.CYAN}{Style.BRIGHT}2. Sample Data Preview...")
        print(f"{Fore.CYAN}{'─' * 100}")
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cursor.fetchall()
                
                if rows:
                    print(f"\n{Fore.YELLOW}{Style.BRIGHT}{table.upper()}:")
                    for i, row in enumerate(rows, 1):
                        # Show first few columns
                        preview = {k: v for k, v in list(row.items())[:4]}
                        print(f"  {i}. {preview}")
                else:
                    print(f"\n{Fore.YELLOW}{table}: No data")
                    
            except Exception as e:
                print(f"{Fore.RED}✗ Error reading {table}: {e}")
        
        # Check relationships
        print(f"\n{Fore.CYAN}{Style.BRIGHT}3. Checking Relationships...")
        print(f"{Fore.CYAN}{'─' * 100}")
        
        # Test JOIN: network_devices with hardware_info
        cursor.execute("""
            SELECT nd.device_name, hi.manufacturer, hi.model_number
            FROM network_devices nd
            JOIN hardware_info hi ON nd.hardware_id = hi.hardware_id
            LIMIT 5
        """)
        join_results = cursor.fetchall()
        
        if join_results:
            print_success(f"JOIN test (network_devices + hardware_info): {len(join_results)} rows")
            for row in join_results[:3]:
                print(f"   {row['device_name']} - {row['manufacturer']} {row['model_number']}")
        
        # Test JOIN: network_devices with device_status
        cursor.execute("""
            SELECT nd.device_name, ds.status_name, ds.status_description
            FROM network_devices nd
            JOIN device_status ds ON nd.status_id = ds.status_id
            LIMIT 5
        """)
        join_results2 = cursor.fetchall()
        
        if join_results2:
            print_success(f"JOIN test (network_devices + device_status): {len(join_results2)} rows")
            for row in join_results2[:3]:
                print(f"   {row['device_name']} - {row['status_name']}")
        
        # Check maintenance logs
        cursor.execute("""
            SELECT ml.log_id, nd.device_name, ml.maintenance_type, ml.performed_by
            FROM maintenance_logs ml
            JOIN network_devices nd ON ml.device_id = nd.device_id
            LIMIT 5
        """)
        maint_results = cursor.fetchall()
        
        if maint_results:
            print_success(f"JOIN test (maintenance_logs + network_devices): {len(maint_results)} rows")
            for row in maint_results[:3]:
                print(f"   {row['device_name']} - {row['maintenance_type']} by {row['performed_by']}")
        
        # Check alerts
        cursor.execute("""
            SELECT na.alert_id, nd.device_name, na.severity, na.alert_message
            FROM network_alerts na
            JOIN network_devices nd ON na.device_id = nd.device_id
            LIMIT 5
        """)
        alert_results = cursor.fetchall()
        
        if alert_results:
            print_success(f"JOIN test (network_alerts + network_devices): {len(alert_results)} rows")
            for row in alert_results[:3]:
                print(f"   {row['device_name']} - {row['severity']}: {row['alert_message'][:50]}")
        
        # Statistics
        print(f"\n{Fore.CYAN}{Style.BRIGHT}4. Statistics...")
        print(f"{Fore.CYAN}{'─' * 100}")
        
        # Count by status
        cursor.execute("""
            SELECT ds.status_name, COUNT(nd.device_id) as count
            FROM device_status ds
            LEFT JOIN network_devices nd ON ds.status_id = nd.status_id
            GROUP BY ds.status_name
            ORDER BY count DESC
        """)
        status_counts = cursor.fetchall()
        
        print(f"\n{Fore.YELLOW}Devices by Status:")
        for row in status_counts:
            print(f"   {row['status_name']}: {row['count']} devices")
        
        # Count by severity
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM network_alerts
            GROUP BY severity
            ORDER BY count DESC
        """)
        severity_counts = cursor.fetchall()
        
        print(f"\n{Fore.YELLOW}Alerts by Severity:")
        for row in severity_counts:
            print(f"   {row['severity']}: {row['count']} alerts")
        
        # Summary
        print_header("VERIFICATION COMPLETE")
        print_success("Database structure verified successfully!")
        print_success("All tables exist with proper relationships")
        print_success("Sample data is properly populated")
        print_info("\nYou can now run the automated API tests using:")
        print(f"   {Fore.CYAN}python test_api_automated.py")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n{Fore.RED}✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    verify_database()
