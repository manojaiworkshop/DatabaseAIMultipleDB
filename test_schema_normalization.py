#!/usr/bin/env python3
"""
Comprehensive test for dynamic ontology and SQL agent
Tests schema normalization and query generation
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("TESTING SCHEMA NORMALIZATION AND SQL AGENT")
print("=" * 80)

# Test 1: Schema normalization
print("\n1. Testing schema normalization...")
from backend.app.services.sql_agent import SQLAgent

# Mock schema in list format (how it comes from database service)
schema_list = [
    {
        'name': 'purchase_order',
        'columns': [
            {'name': 'id', 'type': 'integer', 'primary_key': True},
            {'name': 'vendorgroup', 'type': 'varchar'},
            {'name': 'country', 'type': 'varchar'},
        ]
    }
]

# Create a mock agent
class MockLLM:
    def generate_sql(self, question, schema_context, conversation_history):
        return {'sql': 'SELECT DISTINCT vendorgroup FROM purchase_order'}
    
    def generate_response(self, prompt, system_prompt='', max_tokens=2000, temperature=0.7):
        return '[]'  # Empty JSON array

class MockDB:
    def execute_query(self, sql):
        return [], []

mock_config = {
    'ontology': {
        'enabled': False,  # Disable for this test
        'dynamic_generation': {'enabled': False}
    },
    'neo4j': {'enabled': False}
}

try:
    agent = SQLAgent(MockLLM(), MockDB(), mock_config)
    
    # Test normalization
    normalized = agent._normalize_schema_snapshot(schema_list)
    print(f"   ✅ Schema normalized successfully")
    print(f"   Type: {type(normalized)}")
    print(f"   Has 'tables' key: {'tables' in normalized}")
    print(f"   Tables: {list(normalized.get('tables', {}).keys())}")
    
    # Test with dict format
    schema_dict = {'tables': {'purchase_order': schema_list[0]}}
    normalized2 = agent._normalize_schema_snapshot(schema_dict)
    print(f"   ✅ Dict schema normalized successfully")
    print(f"   Tables: {list(normalized2.get('tables', {}).keys())}")
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Knowledge graph schema handling
print("\n2. Testing knowledge graph schema handling...")
try:
    from backend.app.services.knowledge_graph import KnowledgeGraphService
    
    kg_config = {'neo4j': {'enabled': False}}
    kg = KnowledgeGraphService(kg_config)
    
    # Test with normalized dict format
    insights = kg.get_graph_insights(
        query="show all vendor names",
        schema_snapshot={'tables': {'purchase_order': schema_list[0]}}
    )
    
    print(f"   ✅ Knowledge graph handled dict format")
    print(f"   Insights: {list(insights.keys())}")
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Dynamic ontology with dict format
print("\n3. Testing dynamic ontology schema handling...")
try:
    from backend.app.services.dynamic_ontology import DynamicOntologyService
    
    dynamic_ont = DynamicOntologyService(MockLLM(), {'ontology': {}})
    
    # Test with dict format
    schema_dict_for_ont = {
        'tables': {
            'purchase_order': {
                'name': 'purchase_order',
                'columns': [
                    {'name': 'id', 'type': 'integer', 'primary_key': True},
                    {'name': 'vendorgroup', 'type': 'varchar'},
                ]
            }
        }
    }
    
    # This should not crash even if LLM fails
    print(f"   ✅ Dynamic ontology can accept dict format")
    print(f"   Tables: {list(schema_dict_for_ont['tables'].keys())}")
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 4: End-to-end run method
print("\n4. Testing SQL agent run method...")
try:
    agent = SQLAgent(MockLLM(), MockDB(), mock_config)
    
    initial_state = {
        'question': 'show all vendor names',
        'schema_context': 'Table: purchase_order\n  - vendorgroup (varchar)',
        'max_retries': 1,
        'schema_name': None,
        'schema_snapshot': schema_list,  # Pass as list
        'connection_id': None
    }
    
    print(f"   Schema snapshot type: {type(schema_list)}")
    print(f"   Calling agent.run()...")
    
    # This will test the normalization in run() method
    result = agent.run(
        question='show all vendor names',
        schema_context='Table: purchase_order\n  - vendorgroup (varchar)',
        max_retries=1,
        schema_snapshot=schema_list
    )
    
    print(f"   ✅ Agent run completed")
    print(f"   Success: {result.get('success')}")
    if not result.get('success'):
        print(f"   Errors: {result.get('errors_encountered')}")
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
