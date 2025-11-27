#!/usr/bin/env python3
"""
Quick Fix Test: Verify Neo4j query parameter fix
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.services.ontology_kg_sync import get_ontology_kg_sync_service
import yaml

def test_neo4j_query_fix():
    """Test the fixed Neo4j query"""
    
    print("="*80)
    print("🔧 TESTING NEO4J QUERY PARAMETER FIX")
    print("="*80)
    
    # Load config
    config_file = Path(__file__).parent / 'config.yml'
    if not config_file.exists():
        config_file = Path(__file__).parent / 'app_config.yml'
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Test connection
    neo4j_config = config.get('neo4j', {})
    sync_service = get_ontology_kg_sync_service(config)
    
    if not sync_service.enabled:
        print("❌ Neo4j is not enabled in configuration")
        return False
    
    print("✅ Neo4j connection successful")
    
    # Test the fixed query
    print("\n🔍 Testing ontology insights query...")
    try:
        insights = sync_service.get_ontology_enhanced_insights(
            query="find all unique vendor names",
            connection_id="sap_data_10.35.118.246_5432"
        )
        
        print("✅ Query executed successfully!")
        print(f"\n📊 Results:")
        print(f"   Concepts detected: {len(insights.get('concepts_detected', []))}")
        print(f"   Suggested columns: {len(insights.get('suggested_columns', {}))}")
        print(f"   Semantic mappings: {len(insights.get('semantic_mappings', []))}")
        print(f"   Recommendations: {len(insights.get('recommendations', []))}")
        
        if insights.get('concepts_detected'):
            print(f"\n✅ Concepts found:")
            for concept in insights['concepts_detected']:
                print(f"   • {concept['name']} (confidence: {concept['confidence']:.0%})")
        
        if insights.get('suggested_columns'):
            print(f"\n✅ Suggested columns:")
            for table, cols in insights['suggested_columns'].items():
                print(f"   Table: {table}")
                for col in cols[:3]:
                    print(f"      • {col['column']} ({col.get('confidence', 0):.0%})")
        
        sync_service.close()
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        sync_service.close()
        return False

if __name__ == '__main__':
    success = test_neo4j_query_fix()
    sys.exit(0 if success else 1)
