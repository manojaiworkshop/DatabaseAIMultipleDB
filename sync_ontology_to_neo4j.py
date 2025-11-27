#!/usr/bin/env python3
"""
Ontology to Neo4j Sync Tool

Manually synchronize ontology YAML files to Neo4j Knowledge Graph.

Usage:
    python sync_ontology_to_neo4j.py                    # Sync all ontology files
    python sync_ontology_to_neo4j.py --file path.yml    # Sync specific file
    python sync_ontology_to_neo4j.py --clear             # Clear graph first
    python sync_ontology_to_neo4j.py --test              # Test connection only
"""

import sys
import argparse
import yaml
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.services.ontology_kg_sync import OntologyKGSyncService


def load_config():
    """Load configuration from app_config.yml or config.yml"""
    # Try app_config.yml first (primary config file)
    config_file = Path(__file__).parent / 'app_config.yml'
    
    if not config_file.exists():
        config_file = Path(__file__).parent / 'config.yml'
    
    if not config_file.exists():
        print("❌ Configuration file not found (app_config.yml or config.yml)")
        return None
    
    print(f"📋 Using config file: {config_file.name}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def test_connection(config):
    """Test Neo4j connection"""
    print("\n" + "="*80)
    print("🔍 TESTING NEO4J CONNECTION")
    print("="*80)
    
    neo4j_config = config.get('neo4j', {})
    
    print(f"URI: {neo4j_config.get('uri', 'NOT SET')}")
    print(f"Username: {neo4j_config.get('username', 'NOT SET')}")
    print(f"Enabled: {neo4j_config.get('enabled', False)}")
    
    if not neo4j_config.get('enabled'):
        print("\n⚠️  Neo4j is DISABLED in configuration")
        print("   Enable it in config.yml: neo4j.enabled = true")
        return False
    
    sync_service = OntologyKGSyncService(neo4j_config)
    
    if sync_service.enabled and sync_service.driver:
        print("\n✅ Neo4j connection successful!")
        
        # Get statistics
        try:
            from neo4j import GraphDatabase
            with sync_service.driver.session() as session:
                result = session.run("""
                    MATCH (n)
                    OPTIONAL MATCH ()-[r]->()
                    RETURN 
                        count(DISTINCT n) as node_count,
                        count(DISTINCT r) as rel_count,
                        count(DISTINCT CASE WHEN n:Concept THEN n END) as concept_count,
                        count(DISTINCT CASE WHEN n:Property THEN n END) as property_count
                """)
                record = result.single()
                
                print(f"\n📊 Current Knowledge Graph Statistics:")
                print(f"   Total Nodes: {record['node_count']}")
                print(f"   Total Relationships: {record['rel_count']}")
                print(f"   Concepts: {record['concept_count']}")
                print(f"   Properties: {record['property_count']}")
        except Exception as e:
            print(f"\n⚠️  Could not fetch statistics: {e}")
        
        sync_service.close()
        return True
    else:
        print("\n❌ Neo4j connection failed")
        print("   Check your configuration and ensure Neo4j is running")
        return False


def clear_graph(config):
    """Clear all nodes and relationships from Neo4j"""
    print("\n" + "="*80)
    print("🗑️  CLEARING KNOWLEDGE GRAPH")
    print("="*80)
    
    confirm = input("\n⚠️  This will DELETE ALL nodes and relationships. Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Operation cancelled")
        return False
    
    neo4j_config = config.get('neo4j', {})
    sync_service = OntologyKGSyncService(neo4j_config)
    
    if not sync_service.enabled:
        print("❌ Neo4j is not enabled")
        return False
    
    try:
        with sync_service.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✅ Knowledge Graph cleared successfully")
        sync_service.close()
        return True
    except Exception as e:
        print(f"❌ Failed to clear graph: {e}")
        sync_service.close()
        return False


def sync_single_file(config, file_path):
    """Sync a single ontology file to Neo4j"""
    print("\n" + "="*80)
    print(f"🔄 SYNCING SINGLE FILE: {file_path}")
    print("="*80)
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    neo4j_config = config.get('neo4j', {})
    sync_service = OntologyKGSyncService(neo4j_config)
    
    if not sync_service.enabled:
        print("❌ Neo4j is not enabled in configuration")
        return False
    
    result = sync_service.sync_ontology_file(file_path)
    
    if result.get('success'):
        print("\n✅ SYNC SUCCESSFUL")
        print(f"   Connection ID: {result.get('connection_id')}")
        print(f"   Concepts synced: {result.get('concepts_synced', 0)}")
        print(f"   Properties synced: {result.get('properties_synced', 0)}")
        print(f"   Columns synced: {result.get('columns_synced', 0)}")
        print(f"   Semantic mappings created: {result.get('mappings_created', 0)}")
        print(f"   Relationships synced: {result.get('relationships_synced', 0)}")
        sync_service.close()
        return True
    else:
        print(f"\n❌ SYNC FAILED: {result.get('error')}")
        sync_service.close()
        return False


def sync_all_files(config, ontology_dir=None):
    """Sync all ontology files in a directory"""
    if ontology_dir is None:
        ontology_dir = Path(__file__).parent / 'ontology'
    else:
        ontology_dir = Path(ontology_dir)
    
    print("\n" + "="*80)
    print(f"🔄 SYNCING ALL ONTOLOGY FILES FROM: {ontology_dir}")
    print("="*80)
    
    if not ontology_dir.exists():
        print(f"❌ Ontology directory not found: {ontology_dir}")
        return False
    
    neo4j_config = config.get('neo4j', {})
    sync_service = OntologyKGSyncService(neo4j_config)
    
    if not sync_service.enabled:
        print("❌ Neo4j is not enabled in configuration")
        return False
    
    result = sync_service.sync_all_ontologies(str(ontology_dir))
    
    if result.get('success'):
        print("\n✅ BATCH SYNC SUCCESSFUL")
        print(f"   Files synced: {result.get('files_synced', 0)}")
        print(f"   Files failed: {result.get('files_failed', 0)}")
        print(f"   Total concepts: {result.get('total_concepts', 0)}")
        print(f"   Total semantic mappings: {result.get('total_mappings', 0)}")
        print(f"   Total relationships: {result.get('total_relationships', 0)}")
        
        if result.get('errors'):
            print("\n⚠️  Errors:")
            for error in result['errors']:
                print(f"   - {error['file']}: {error['error']}")
        
        sync_service.close()
        return True
    else:
        print(f"\n❌ BATCH SYNC FAILED: {result.get('error')}")
        sync_service.close()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Sync ontology YAML files to Neo4j Knowledge Graph',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Sync all ontology files
  %(prog)s --test                    # Test Neo4j connection
  %(prog)s --file ontology.yml       # Sync specific file
  %(prog)s --clear                   # Clear graph first, then sync
  %(prog)s --dir /path/to/ontology   # Sync files from specific directory
        """
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='Path to specific ontology YAML file to sync'
    )
    
    parser.add_argument(
        '--dir',
        type=str,
        help='Directory containing ontology files (default: ./ontology/)'
    )
    
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear all nodes and relationships before syncing'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test Neo4j connection only (no sync)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    print("\n📋 Loading configuration...")
    config = load_config()
    
    if not config:
        sys.exit(1)
    
    # Test connection if requested
    if args.test:
        success = test_connection(config)
        sys.exit(0 if success else 1)
    
    # Clear graph if requested
    if args.clear:
        if not clear_graph(config):
            sys.exit(1)
    
    # Sync files
    if args.file:
        # Sync single file
        success = sync_single_file(config, args.file)
    else:
        # Sync all files
        success = sync_all_files(config, args.dir)
    
    if success:
        print("\n" + "="*80)
        print("🎉 SYNC COMPLETE!")
        print("="*80)
        print("\nYour Knowledge Graph is now enhanced with semantic ontology mappings.")
        print("The SQL Agent will now receive intelligent column recommendations!")
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("❌ SYNC FAILED")
        print("="*80)
        sys.exit(1)


if __name__ == '__main__':
    main()
