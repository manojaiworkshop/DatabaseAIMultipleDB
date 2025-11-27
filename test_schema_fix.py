"""
Test script to verify schema detection from all schemas (not just 'public')
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.database import DatabaseService
import json

# Initialize database service
db = DatabaseService()

# Set connection to the user's database
# NOTE: Update these credentials to match your actual database
db.set_connection(
    host='localhost',
    port=5432,
    database='postgres',  # Update this
    username='postgres',  # Update this
    password='your_password',  # Update this
    use_docker=False
)

print("=" * 80)
print("TESTING SCHEMA DETECTION - ALL SCHEMAS (NOT JUST 'public')")
print("=" * 80)

try:
    # Get database snapshot
    snapshot = db.get_database_snapshot()
    
    print(f"\n✅ Database: {snapshot['database_name']}")
    print(f"✅ Total Tables: {snapshot['total_tables']}")
    print(f"✅ Total Views: {snapshot['total_views']}")
    print(f"✅ Timestamp: {snapshot['timestamp']}")
    
    print("\n" + "=" * 80)
    print("TABLES FOUND (with schema names):")
    print("=" * 80)
    
    if snapshot['tables']:
        for table in snapshot['tables']:
            schema_name = table.get('schema_name', 'unknown')
            table_name = table.get('table_name', 'unknown')
            full_name = table.get('full_name', f"{schema_name}.{table_name}")
            column_count = len(table.get('columns', []))
            sample_count = len(table.get('sample_data', []))
            
            print(f"\n📊 {full_name}")
            print(f"   Schema: {schema_name}")
            print(f"   Table: {table_name}")
            print(f"   Columns: {column_count}")
            print(f"   Sample rows: {sample_count}")
            
            # Show first 5 columns
            if table.get('columns'):
                print("   First 5 columns:")
                for col in table['columns'][:5]:
                    col_name = col.get('column_name', 'unknown')
                    col_type = col.get('data_type', 'unknown')
                    nullable = col.get('is_nullable', 'YES')
                    print(f"      - {col_name} ({col_type}) {'NULL' if nullable == 'YES' else 'NOT NULL'}")
                
                if column_count > 5:
                    print(f"      ... and {column_count - 5} more columns")
    else:
        print("\n⚠️  NO TABLES FOUND!")
        print("This means the database is empty or connection failed.")
    
    print("\n" + "=" * 80)
    print("EXPECTED RESULT:")
    print("=" * 80)
    print("✅ Should show 'sap_data.purchase_order' table")
    print("✅ Should show 37 columns (vendorgroup, country, clausedescription, etc.)")
    print("✅ Should show 3 sample data rows")
    print("✅ Should NOT show only 'public' schema tables")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
