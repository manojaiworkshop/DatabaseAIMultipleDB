#!/usr/bin/env python3
"""
Test script for Dynamic Ontology Generation
Tests the full flow from database schema to ontology creation
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.database import DatabaseService
from app.services.llm import LLMService
from app.services.dynamic_ontology import DynamicOntologyService
from app.core.config import load_config


class OntologyTester:
    def __init__(self):
        self.config = load_config()
        self.db_service = DatabaseService()
        self.llm_service = LLMService(self.config)
        self.ontology_service = None
        
    async def test_database_connection(self):
        """Test 1: Verify database connection and schema extraction"""
        print("\n" + "="*60)
        print("TEST 1: Database Connection & Schema Extraction")
        print("="*60)
        
        # Use connection from config or environment
        connection_params = {
            "host": os.getenv("DB_HOST", "192.168.1.2"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "testing"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres")
        }
        
        print(f"\n📡 Connecting to: {connection_params['database']} @ {connection_params['host']}")
        
        try:
            self.db_service.set_connection(**connection_params)
            result = await self.db_service.test_connection()
            
            if result["success"]:
                print(f"✅ Connection successful!")
                print(f"   Database: {result['database']}")
                print(f"   Version: {result['version']}")
            else:
                print(f"❌ Connection failed: {result.get('message')}")
                return False
                
        except Exception as e:
            print(f"❌ Exception during connection: {e}")
            return False
        
        # Get schema snapshot
        print("\n📊 Extracting database schema...")
        try:
            snapshot = await self.db_service.get_database_snapshot()
            tables = snapshot.get("tables", [])
            
            print(f"✅ Schema extracted successfully!")
            print(f"   Total tables: {len(tables)}")
            
            if tables:
                print("\n   Sample tables:")
                for table in tables[:5]:
                    print(f"     • {table['name']} ({len(table.get('columns', []))} columns)")
            else:
                print("   ⚠️  No tables found in schema!")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Failed to extract schema: {e}")
            return False
    
    async def test_llm_structured_generation(self):
        """Test 2: Verify LLM can generate structured JSON"""
        print("\n" + "="*60)
        print("TEST 2: LLM Structured JSON Generation")
        print("="*60)
        
        # Check if generate_structured exists
        if not hasattr(self.llm_service, 'generate_structured'):
            print("❌ LLMService does not have 'generate_structured' method!")
            print("   This method needs to be added to backend/app/services/llm.py")
            return False
        
        # Simple test prompt
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant. Return only valid JSON."},
            {"role": "user", "content": """Generate a JSON object representing 2 database concepts.
Format:
[
  {
    "name": "Customer",
    "description": "A person who purchases products",
    "confidence": 0.95
  },
  {
    "name": "Order",
    "description": "A purchase transaction",
    "confidence": 0.90
  }
]

Return ONLY valid JSON, no markdown, no explanation."""}
        ]
        
        print("\n🤖 Testing LLM structured generation...")
        print(f"   Provider: {self.config['llm']['provider']}")
        print(f"   Model: {self.config.get(self.config['llm']['provider'], {}).get('model', 'unknown')}")
        
        try:
            result = await self.llm_service.generate_structured(test_messages, max_tokens=512)
            
            if isinstance(result, (list, dict)):
                print(f"✅ LLM returned valid structured data!")
                print(f"   Type: {type(result).__name__}")
                print(f"   Sample: {json.dumps(result, indent=2)[:200]}...")
                return True
            else:
                print(f"❌ LLM returned unexpected type: {type(result)}")
                return False
                
        except ValueError as e:
            print(f"❌ Failed to parse LLM response as JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ Exception during LLM generation: {e}")
            return False
    
    async def test_ontology_generation(self):
        """Test 3: Generate actual ontology from database"""
        print("\n" + "="*60)
        print("TEST 3: Dynamic Ontology Generation")
        print("="*60)
        
        # Initialize ontology service
        print("\n🧬 Initializing Dynamic Ontology Service...")
        try:
            self.ontology_service = DynamicOntologyService(
                llm_service=self.llm_service,
                db_service=self.db_service,
                config=self.config
            )
            print("✅ Ontology service initialized")
        except Exception as e:
            print(f"❌ Failed to initialize ontology service: {e}")
            return False
        
        # Generate ontology
        print("\n🔄 Generating ontology...")
        try:
            ontology = await self.ontology_service.generate_ontology()
            
            # Validate structure
            if not ontology:
                print("❌ No ontology returned!")
                return False
            
            concepts = ontology.get("concepts", [])
            properties = ontology.get("properties", [])
            relationships = ontology.get("relationships", [])
            
            print(f"\n✅ Ontology generated successfully!")
            print(f"   Concepts: {len(concepts)}")
            print(f"   Properties: {len(properties)}")
            print(f"   Relationships: {len(relationships)}")
            
            # Show sample concepts
            if concepts:
                print("\n   Sample concepts:")
                for concept in concepts[:3]:
                    print(f"     • {concept.get('name', 'unnamed')} (confidence: {concept.get('confidence', 0):.2f})")
                    if 'tables' in concept:
                        print(f"       Tables: {', '.join(concept['tables'])}")
            else:
                print("\n   ⚠️  No concepts generated!")
            
            # Show sample relationships
            if relationships:
                print("\n   Sample relationships:")
                for rel in relationships[:3]:
                    print(f"     • {rel.get('from_concept')} → {rel.get('to_concept')} ({rel.get('relationship_type')})")
            
            return len(concepts) > 0
            
        except Exception as e:
            print(f"❌ Failed to generate ontology: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_ontology_export(self):
        """Test 4: Verify ontology files are created"""
        print("\n" + "="*60)
        print("TEST 4: Ontology Export Validation")
        print("="*60)
        
        ontology_dir = Path("ontology")
        
        print(f"\n📁 Checking ontology directory: {ontology_dir.absolute()}")
        
        if not ontology_dir.exists():
            print("❌ Ontology directory does not exist!")
            return False
        
        # Find latest files
        yaml_files = sorted(ontology_dir.glob("*.yml"), key=os.path.getmtime, reverse=True)
        owl_files = sorted(ontology_dir.glob("*.owl"), key=os.path.getmtime, reverse=True)
        
        print(f"   YAML files: {len(yaml_files)}")
        print(f"   OWL files: {len(owl_files)}")
        
        if not yaml_files:
            print("❌ No YAML files found!")
            return False
        
        # Check latest YAML
        latest_yaml = yaml_files[0]
        print(f"\n📄 Checking latest YAML: {latest_yaml.name}")
        
        try:
            import yaml
            with open(latest_yaml, 'r') as f:
                data = yaml.safe_load(f)
            
            concepts = data.get("concepts", [])
            properties = data.get("properties", [])
            relationships = data.get("relationships", [])
            
            print(f"   Concepts: {len(concepts)}")
            print(f"   Properties: {len(properties)}")
            print(f"   Relationships: {len(relationships)}")
            
            if len(concepts) == 0:
                print("   ⚠️  YAML file has 0 concepts!")
                return False
            
            print("✅ YAML file is valid and contains data")
            
        except Exception as e:
            print(f"❌ Failed to parse YAML: {e}")
            return False
        
        # Check latest OWL
        if owl_files:
            latest_owl = owl_files[0]
            print(f"\n🦉 Checking latest OWL: {latest_owl.name}")
            
            try:
                with open(latest_owl, 'r') as f:
                    content = f.read()
                
                # Basic validation
                if '<owl:Ontology' in content and '</rdf:RDF>' in content:
                    # Count classes
                    class_count = content.count('<owl:Class')
                    property_count = content.count('<owl:ObjectProperty') + content.count('<owl:DatatypeProperty')
                    
                    print(f"   OWL Classes: {class_count}")
                    print(f"   OWL Properties: {property_count}")
                    
                    if class_count == 0:
                        print("   ⚠️  OWL file has 0 classes!")
                        return False
                    
                    print("✅ OWL file is valid and contains data")
                else:
                    print("❌ OWL file structure is invalid!")
                    return False
                    
            except Exception as e:
                print(f"❌ Failed to read OWL: {e}")
                return False
        else:
            print("\n⚠️  No OWL files found")
        
        return True
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "🧪 " * 20)
        print("DYNAMIC ONTOLOGY GENERATION TEST SUITE")
        print("🧪 " * 20)
        
        results = []
        
        # Test 1: Database connection
        results.append(("Database Connection", await self.test_database_connection()))
        
        if not results[0][1]:
            print("\n❌ Cannot proceed without database connection")
            return False
        
        # Test 2: LLM structured generation
        results.append(("LLM Structured Generation", await self.test_llm_structured_generation()))
        
        if not results[1][1]:
            print("\n⚠️  Warning: LLM structured generation test failed")
            print("   The generate_structured method may need to be implemented")
        
        # Test 3: Ontology generation
        results.append(("Ontology Generation", await self.test_ontology_generation()))
        
        # Test 4: Export validation
        results.append(("Ontology Export", await self.test_ontology_export()))
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result:
                passed += 1
        
        print(f"\nTotal: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            print("\n🎉 All tests passed! Ontology generation is working correctly.")
            return True
        else:
            print("\n⚠️  Some tests failed. Review the output above for details.")
            return False


async def main():
    """Main test runner"""
    tester = OntologyTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
