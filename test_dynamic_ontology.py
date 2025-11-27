#!/usr/bin/env python3
"""
Test Dynamic Ontology Generation
"""
import sys
sys.path.insert(0, 'backend')

from app.config import load_config
from app.services.llm_service import get_llm_service
from app.services.dynamic_ontology import get_dynamic_ontology_service

def test_dynamic_ontology():
    """Test the dynamic ontology generation"""
    print("=" * 60)
    print("Testing Dynamic Ontology Generation")
    print("=" * 60)
    
    # Load config
    config = load_config()
    print("✓ Config loaded")
    
    # Initialize LLM service
    llm_service = get_llm_service(config)
    print(f"✓ LLM service initialized (provider: {config['llm']['provider']})")
    
    # Initialize dynamic ontology service
    dynamic_ontology = get_dynamic_ontology_service(llm_service, config)
    print("✓ Dynamic ontology service initialized")
    
    # Create mock schema snapshot (like what db_service returns)
    mock_schema = [
        {
            'name': 'purchase_order',
            'columns': [
                {'name': 'id', 'type': 'integer', 'primary_key': True, 'nullable': False},
                {'name': 'vendorgroup', 'type': 'varchar', 'nullable': True},
                {'name': 'country', 'type': 'varchar', 'nullable': True},
                {'name': 'total_amount', 'type': 'numeric', 'nullable': True},
                {'name': 'order_date', 'type': 'date', 'nullable': True},
            ]
        }
    ]
    
    print("\n" + "-" * 60)
    print("Test Schema:")
    print(f"  Table: purchase_order")
    print(f"  Columns: id, vendorgroup, country, total_amount, order_date")
    print("-" * 60)
    
    # Generate ontology
    print("\n🤖 Generating dynamic ontology...")
    try:
        ontology = dynamic_ontology.generate_ontology(
            schema_snapshot=mock_schema,
            connection_id='test_connection',
            force_regenerate=True
        )
        
        print("\n✅ Ontology generated successfully!")
        print(f"\nMetadata:")
        print(f"  Concepts: {ontology['metadata']['concept_count']}")
        print(f"  Properties: {ontology['metadata']['property_count']}")
        print(f"  Relationships: {ontology['metadata']['relationship_count']}")
        
        print(f"\n📚 Concepts:")
        for concept in ontology['concepts'][:5]:
            print(f"  • {concept['name']}: {concept['description']}")
            if concept.get('tables'):
                print(f"    Tables: {', '.join(concept['tables'])}")
        
        print(f"\n🎯 Property Mappings:")
        for prop in ontology['properties'][:10]:
            print(f"  • {prop['table']}.{prop['column']} → {prop['concept']}.{prop['property_name']}")
            print(f"    Meaning: {prop['semantic_meaning']}")
        
        print(f"\n🔗 Relationships:")
        for rel in ontology['relationships']:
            print(f"  • {rel['from_concept']} {rel['relationship_type']} {rel['to_concept']}")
        
        print("\n" + "=" * 60)
        print("✅ Dynamic Ontology Test PASSED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_dynamic_ontology()
    sys.exit(0 if success else 1)
