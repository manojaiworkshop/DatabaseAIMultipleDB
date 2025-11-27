#!/usr/bin/env python3
"""Quick Neo4j connection test"""

import yaml
from pathlib import Path

try:
    from neo4j import GraphDatabase
    
    # Load config
    config_file = Path(__file__).parent / 'app_config.yml'
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    neo4j_config = config.get('neo4j', {})
    
    print("="*80)
    print("🔍 NEO4J CONNECTION TEST")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Enabled: {neo4j_config.get('enabled')}")
    print(f"  URI: {neo4j_config.get('uri')}")
    print(f"  Username: {neo4j_config.get('username')}")
    print(f"  Password: {'*' * len(neo4j_config.get('password', ''))}")
    
    # Try to connect
    print(f"\n🔌 Attempting connection...")
    driver = GraphDatabase.driver(
        neo4j_config.get('uri'),
        auth=(neo4j_config.get('username'), neo4j_config.get('password'))
    )
    
    # Test query
    with driver.session() as session:
        result = session.run("RETURN 1 as test")
        record = result.single()
        print(f"✅ Connection successful! Test query returned: {record['test']}")
        
        # Check if any data exists
        result = session.run("MATCH (n) RETURN count(n) as node_count")
        record = result.single()
        print(f"📊 Current nodes in database: {record['node_count']}")
    
    driver.close()
    print("\n✅ Neo4j is ready to use!")
    print("="*80)
    
except ImportError:
    print("❌ neo4j package not installed. Install with: pip install neo4j")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nPossible solutions:")
    print("1. Check if Neo4j container is fully started (wait a minute)")
    print("2. Verify password in app_config.yml matches Neo4j")
    print("3. Try restarting Neo4j: docker restart neo4j-community")
