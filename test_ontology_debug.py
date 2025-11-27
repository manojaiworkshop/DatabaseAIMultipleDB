#!/usr/bin/env python3
"""
Test script to verify ontology debug instrumentation
Run this to see if debug logging is working correctly
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_database_snapshot():
    """Test database snapshot retrieval"""
    print("="*80)
    print("TEST 1: Database Snapshot Retrieval")
    print("="*80)
    
    try:
        from app.services.database import db_service
        
        # Check if connected
        if not db_service.connection_params:
            print("❌ ERROR: No database connection")
            print("Please connect to database first")
            return False
        
        print(f"✅ Connected to: {db_service.connection_params.get('database')}")
        
        # Get snapshot
        snapshot = db_service.get_database_snapshot()
        
        # Print results
        print(f"\n📊 Snapshot Structure:")
        print(f"  Keys: {list(snapshot.keys())}")
        print(f"  Database: {snapshot.get('database_name')}")
        print(f"  Total tables: {snapshot.get('total_tables')}")
        print(f"  Total views: {snapshot.get('total_views')}")
        
        tables = snapshot.get('tables', [])
        print(f"\n📋 Tables Found ({len(tables)}):")
        
        if not tables:
            print("  ⚠️  NO TABLES FOUND!")
            return False
        
        for i, table in enumerate(tables[:5], 1):
            schema_name = table.get('schema_name', 'public')
            table_name = table.get('table_name', 'unknown')
            full_name = table.get('full_name', f"{schema_name}.{table_name}")
            columns = table.get('columns', [])
            print(f"  {i}. {full_name} ({len(columns)} columns)")
            
            # Show first 3 columns
            for j, col in enumerate(columns[:3], 1):
                col_name = col.get('column_name', 'unknown')
                col_type = col.get('data_type', 'unknown')
                print(f"      {j}. {col_name} ({col_type})")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schema_summary():
    """Test schema summary generation"""
    print("\n" + "="*80)
    print("TEST 2: Schema Summary Generation")
    print("="*80)
    
    try:
        from app.services.database import db_service
        from app.services.dynamic_ontology import DynamicOntologyService
        from app.services.llm import LLMService
        from app.config import load_config
        
        config = load_config()
        
        # Initialize services
        llm = LLMService(config)
        ontology_service = DynamicOntologyService(llm, config)
        
        # Get snapshot
        snapshot = db_service.get_database_snapshot()
        
        # Generate summary
        print("\n🔄 Generating schema summary...")
        summary = ontology_service._summarize_schema(snapshot)
        
        print("\n📄 Schema Summary Preview (first 1000 chars):")
        print("-" * 80)
        print(summary[:1000])
        print("-" * 80)
        
        print(f"\n✅ Summary length: {len(summary)} characters")
        
        # Check for actual table names
        expected_tables = [
            'device_status',
            'hardware_info', 
            'maintenance_logs',
            'network_alerts',
            'network_devices'
        ]
        
        print("\n🔍 Checking for expected tables in summary:")
        found_count = 0
        for table_name in expected_tables:
            if table_name in summary:
                print(f"  ✅ {table_name} - FOUND")
                found_count += 1
            else:
                print(f"  ❌ {table_name} - NOT FOUND")
        
        print(f"\n📊 Result: {found_count}/{len(expected_tables)} tables found in summary")
        
        return found_count == len(expected_tables)
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_debug_file():
    """Check if debug file exists and has content"""
    print("\n" + "="*80)
    print("TEST 3: Debug File Check")
    print("="*80)
    
    debug_file = "debug_ontology_prompt.txt"
    
    if os.path.exists(debug_file):
        size = os.path.getsize(debug_file)
        print(f"✅ File exists: {debug_file} ({size} bytes)")
        
        with open(debug_file, 'r') as f:
            content = f.read()
            print(f"\n📄 File preview (first 500 chars):")
            print("-" * 80)
            print(content[:500])
            print("-" * 80)
        
        return True
    else:
        print(f"⚠️  File not found: {debug_file}")
        print("This file will be created when ontology is generated")
        return None

if __name__ == "__main__":
    print("\n🔍 ONTOLOGY DEBUG INSTRUMENTATION TEST")
    print("=" * 80)
    
    results = {}
    
    # Run tests
    results['snapshot'] = test_database_snapshot()
    
    if results['snapshot']:
        results['summary'] = test_schema_summary()
    else:
        print("\n⚠️  Skipping summary test (database snapshot failed)")
        results['summary'] = False
    
    results['debug_file'] = test_debug_file()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else ("⚠️  SKIP" if result is None else "❌ FAIL")
        print(f"{test_name:20s}: {status}")
    
    # Overall result
    all_pass = all(r for r in results.values() if r is not None)
    
    print("\n" + "="*80)
    if all_pass:
        print("✅ ALL TESTS PASSED - Debug instrumentation is working")
        print("\nNext steps:")
        print("1. Restart backend: pkill -f run_backend && python run_backend.py &")
        print("2. Generate ontology from UI")
        print("3. Check debug_ontology_prompt.txt file")
        print("4. Check backend logs for DEBUG markers")
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
    print("="*80)
