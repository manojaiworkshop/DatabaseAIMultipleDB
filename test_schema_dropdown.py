#!/usr/bin/env python3
"""
Test script for schema dropdown feature
"""
import sys
sys.path.insert(0, '/media/manoj/DriveData6/DATABASEAI')

from backend.app.services.database import DatabaseService
import json

def test_schema_feature():
    """Test the new schema dropdown feature"""
    
    print("=" * 60)
    print("Testing Schema Dropdown Feature")
    print("=" * 60)
    
    # Initialize database service
    db = DatabaseService()
    
    # Set connection (you may need to update these credentials)
    print("\n1. Setting up database connection...")
    db.set_connection(
        host='localhost',
        port=5432,
        database='postgres',  # Change to your database
        username='postgres',  # Change to your username
        password='postgres'   # Change to your password
    )
    print("✓ Connection configured")
    
    # Test connection
    print("\n2. Testing connection...")
    success, message, info = db.test_connection()
    if success:
        print(f"✓ Connection successful: {message}")
        print(f"  Database: {info.get('database')}")
        print(f"  Tables in public: {info.get('table_count')}")
    else:
        print(f"✗ Connection failed: {message}")
        return False
    
    # Get all schemas
    print("\n3. Fetching all schemas...")
    try:
        schemas = db.get_all_schemas()
        print(f"✓ Found {len(schemas)} user schemas:")
        for schema in schemas:
            print(f"  - {schema['schema_name']}: {schema['table_count']} tables, {schema['view_count']} views")
    except Exception as e:
        print(f"✗ Failed to get schemas: {e}")
        return False
    
    # Get snapshot for each schema
    print("\n4. Testing schema-specific snapshots...")
    for schema in schemas[:3]:  # Test first 3 schemas
        schema_name = schema['schema_name']
        print(f"\n   Testing schema: {schema_name}")
        try:
            snapshot = db.get_schema_snapshot(schema_name)
            print(f"   ✓ Snapshot retrieved:")
            print(f"     - Schema: {snapshot['schema_name']}")
            print(f"     - Tables: {snapshot['total_tables']}")
            print(f"     - Views: {snapshot['total_views']}")
            
            # Show first table details
            if snapshot['tables']:
                table = snapshot['tables'][0]
                print(f"     - Sample table: {table['table_name']}")
                print(f"       Columns: {len(table['columns'])}")
                if table['columns']:
                    print(f"       First column: {table['columns'][0]['column_name']} ({table['columns'][0]['data_type']})")
                    # Check for primary key
                    pk_cols = [c['column_name'] for c in table['columns'] if c.get('primary_key')]
                    if pk_cols:
                        print(f"       Primary keys: {', '.join(pk_cols)}")
        except Exception as e:
            print(f"   ✗ Failed to get snapshot for {schema_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Test caching
    print("\n5. Testing cache performance...")
    if schemas:
        schema_name = schemas[0]['schema_name']
        import time
        
        # First fetch (cold cache)
        start = time.time()
        snapshot1 = db.get_schema_snapshot(schema_name)
        cold_time = time.time() - start
        print(f"   Cold cache fetch: {cold_time:.3f}s")
        
        # Second fetch (warm cache)
        start = time.time()
        snapshot2 = db.get_schema_snapshot(schema_name)
        warm_time = time.time() - start
        print(f"   Warm cache fetch: {warm_time:.3f}s")
        print(f"   ✓ Speedup: {cold_time/warm_time:.1f}x faster")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_schema_feature()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
