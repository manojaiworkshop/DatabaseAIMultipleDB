"""
Ontology to Knowledge Graph Sync Service

Synchronizes ontology definitions (YAML files) with Neo4j Knowledge Graph
to create an intelligent semantic layer that combines:
1. Ontology concepts and properties
2. Database schema (tables/columns)
3. Semantic relationships and mappings

This enables the knowledge graph to provide ontology-enhanced recommendations.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


class OntologyKGSyncService:
    """
    Synchronizes ontology data with Neo4j Knowledge Graph
    
    Creates a rich semantic network:
    - Concept nodes (Vendor, Product, Order)
    - Property nodes (name, location, price)
    - Column nodes (vendorgroup, country, totalinrpo)
    - Semantic relationships (maps_to, has_property, similar_to)
    """
    
    def __init__(self, neo4j_config: Dict[str, Any]):
        """Initialize sync service with Neo4j configuration"""
        self.config = neo4j_config
        self.driver = None
        self.enabled = neo4j_config.get('enabled', False)
        
        if self.enabled:
            self._connect()
    
    def _connect(self):
        """Establish Neo4j connection"""
        try:
            uri = self.config.get('uri', 'bolt://localhost:7687')
            username = self.config.get('username', 'neo4j')
            password = self.config.get('password', 'password')
            
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"✅ Ontology sync service connected to Neo4j at {uri}")
            
        except (ServiceUnavailable, Exception) as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            self.enabled = False
            self.driver = None
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Ontology sync service connection closed")
    
    def sync_ontology_file(self, ontology_file_path: str) -> Dict[str, Any]:
        """
        Sync a single ontology YAML file to Neo4j
        
        Args:
            ontology_file_path: Path to ontology YAML file
            
        Returns:
            Sync statistics dictionary
        """
        if not self.enabled or not self.driver:
            return {
                'success': False,
                'error': 'Neo4j not enabled or not connected'
            }
        
        try:
            # Load ontology YAML
            with open(ontology_file_path, 'r') as f:
                ontology_data = yaml.safe_load(f)
            
            logger.info(f"📖 Loaded ontology from: {ontology_file_path}")
            
            # Extract metadata
            metadata = ontology_data.get('ontology', {}).get('metadata', {})
            connection_id = metadata.get('connection_id', 'unknown')
            
            # Extract ontology components
            concepts = ontology_data.get('ontology', {}).get('concepts', {})
            relationships = ontology_data.get('ontology', {}).get('relationships', [])
            rules = ontology_data.get('ontology', {}).get('rules', [])
            
            logger.info(f"📊 Ontology contains: {len(concepts)} concepts, {len(relationships)} relationships")
            
            stats = {
                'success': True,
                'connection_id': connection_id,
                'concepts_synced': 0,
                'properties_synced': 0,
                'columns_synced': 0,
                'relationships_synced': 0,
                'mappings_created': 0
            }
            
            with self.driver.session() as session:
                # 1. Create Database/Connection node
                session.run("""
                    MERGE (db:DatabaseConnection {id: $connection_id})
                    SET db.last_synced = datetime(),
                        db.ontology_file = $file_path
                """, connection_id=connection_id, file_path=ontology_file_path)
                
                # 2. Create Concept nodes
                for concept_name, concept_data in concepts.items():
                    description = concept_data.get('description', '')
                    confidence = concept_data.get('confidence', 1.0)
                    properties = concept_data.get('properties', [])
                    tables = concept_data.get('tables', [])
                    
                    # Create Concept node
                    session.run("""
                        MERGE (c:Concept {name: $concept_name, connection: $connection_id})
                        SET c.description = $description,
                            c.confidence = $confidence,
                            c.property_count = $prop_count,
                            c.table_count = $table_count,
                            c.last_updated = datetime()
                        WITH c
                        MATCH (db:DatabaseConnection {id: $connection_id})
                        MERGE (db)-[:HAS_CONCEPT]->(c)
                    """, concept_name=concept_name,
                         connection_id=connection_id,
                         description=description,
                         confidence=confidence,
                         prop_count=len(properties),
                         table_count=len(tables))
                    
                    stats['concepts_synced'] += 1
                    
                    # 3. Create Property nodes for each concept property
                    for prop_name in properties:
                        session.run("""
                            MATCH (c:Concept {name: $concept_name, connection: $connection_id})
                            MERGE (p:Property {name: $prop_name, concept: $concept_name})
                            SET p.last_updated = datetime()
                            MERGE (c)-[:HAS_PROPERTY]->(p)
                        """, concept_name=concept_name,
                             connection_id=connection_id,
                             prop_name=prop_name)
                        
                        stats['properties_synced'] += 1
                        
                        # 4. Create semantic mappings: Property -> Column
                        # This is the KEY enhancement: linking ontology to physical schema
                        for table_name in tables:
                            # Extract schema and table
                            if '.' in table_name:
                                schema, table = table_name.split('.', 1)
                            else:
                                schema, table = 'public', table_name
                            
                            # Create semantic mapping based on property name
                            # Match property to likely columns (fuzzy matching)
                            self._create_semantic_column_mappings(
                                session,
                                concept_name,
                                prop_name,
                                schema,
                                table,
                                connection_id,
                                stats
                            )
                    
                    # 5. Link Concept to Tables
                    for table_name in tables:
                        if '.' in table_name:
                            schema, table = table_name.split('.', 1)
                        else:
                            schema, table = 'public', table_name
                        
                        # Try to find existing Table node from schema sync
                        session.run("""
                            MATCH (c:Concept {name: $concept_name, connection: $connection_id})
                            OPTIONAL MATCH (t:Table {name: $table_name})
                            WITH c, t
                            WHERE t IS NOT NULL
                            MERGE (c)-[r:MAPS_TO_TABLE]->(t)
                            SET r.confidence = $confidence
                        """, concept_name=concept_name,
                             connection_id=connection_id,
                             table_name=table,
                             confidence=confidence)
                
                # 6. Create Relationship edges between concepts
                for rel in relationships:
                    from_concept = rel.get('from', '')
                    to_concept = rel.get('to', '')
                    rel_type = rel.get('type', 'related_to')
                    rel_confidence = rel.get('confidence', 1.0)
                    via_tables = rel.get('via_tables', [])
                    
                    if from_concept and to_concept:
                        session.run("""
                            MATCH (c1:Concept {name: $from_concept, connection: $connection_id})
                            MATCH (c2:Concept {name: $to_concept, connection: $connection_id})
                            MERGE (c1)-[r:SEMANTIC_RELATIONSHIP]->(c2)
                            SET r.type = $rel_type,
                                r.confidence = $confidence,
                                r.via_tables = $via_tables,
                                r.last_updated = datetime()
                        """, from_concept=from_concept,
                             to_concept=to_concept,
                             connection_id=connection_id,
                             rel_type=rel_type,
                             confidence=rel_confidence,
                             via_tables=via_tables)
                        
                        stats['relationships_synced'] += 1
                
                # 7. Create synonym mappings for fuzzy search
                self._create_synonym_index(session, concepts, connection_id)
                
                logger.info(f"✅ Ontology sync complete: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"❌ Failed to sync ontology: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_semantic_column_mappings(
        self,
        session,
        concept_name: str,
        property_name: str,
        schema: str,
        table: str,
        connection_id: str,
        stats: Dict[str, Any]
    ):
        """
        Create intelligent semantic mappings between Properties and Columns
        
        This is the CORE INTELLIGENCE that links business terms to database columns
        
        Examples:
        - Vendor.name → vendorgroup, vendorname, vendor_id
        - Vendor.location → country, region
        - Order.total → totalinrpo, netvalue
        """
        
        # Define semantic mapping rules (can be expanded)
        mapping_rules = {
            # Vendor mappings
            'Vendor.name': ['vendorgroup', 'vendorname', 'vendor_name', 'supplier_name', 'vendor_id', 'supplierid'],
            'Vendor.location': ['country', 'region', 'location', 'vendor_country'],
            'Vendor.category': ['vendorcategory', 'vendor_category', 'vendor_type', 'vendortype'],
            'Vendor.id': ['vendorid', 'vendor_id', 'supplier_id', 'supplierid'],
            'Vendor.type': ['vendortype', 'vendor_type', 'vendorcategory'],
            'Vendor.industry': ['vendorindustry', 'vendor_industry'],
            
            # Order/Purchase mappings
            'Order.total': ['totalinrpo', 'netvalue', 'total_value', 'order_total', 'amount'],
            'Order.value': ['netvalue', 'totalinrpo', 'net_value', 'value'],
            'Order.tax': ['netvaluewithtax', 'tax_amount', 'tax'],
            'Order.pending': ['totalinrpending', 'pending_amount'],
            'Order.id': ['id', 'order_id', 'purchasingdocument', 'document_id'],
            'Order.date': ['createdon', 'creationdate', 'postingdate', 'order_date'],
            'Order.currency': ['currency', 'currency_code'],
            
            # PurchaseOrder mappings
            'PurchaseOrder.id': ['id', 'purchasingdocument', 'po_number'],
            'PurchaseOrder.value': ['totalinrpo', 'netvalue'],
            'PurchaseOrder.status': ['status', 'po_status'],
            
            # Generic mappings
            'name': ['name', '_name', 'title', 'label'],
            'id': ['id', '_id', 'identifier'],
            'date': ['date', '_date', '_on', 'created_at'],
            'location': ['country', 'region', 'location', 'city'],
        }
        
        # Build mapping key
        mapping_key = f"{concept_name}.{property_name}"
        
        # Get potential column matches
        potential_columns = mapping_rules.get(mapping_key, [])
        
        # Also try generic property name
        if not potential_columns:
            potential_columns = mapping_rules.get(property_name, [])
        
        # If still no matches, use fuzzy matching on property name
        if not potential_columns:
            potential_columns = [
                f"{property_name}",
                f"{property_name.lower()}",
                f"{concept_name.lower()}{property_name}",
                f"{concept_name.lower()}_{property_name.lower()}"
            ]
        
        # Create mappings for each potential column
        for column_pattern in potential_columns:
            # Find matching columns in the table
            result = session.run("""
                MATCH (t:Table {name: $table_name})
                MATCH (t)-[:HAS_COLUMN]->(col:Column)
                WHERE col.name =~ $pattern
                RETURN col.name as column_name, col.data_type as data_type
            """, table_name=table, pattern=f"(?i).*{column_pattern}.*")
            
            for record in result:
                column_name = record['column_name']
                data_type = record.get('data_type', 'unknown')
                
                # Calculate confidence based on match quality
                confidence = self._calculate_mapping_confidence(
                    property_name,
                    column_name,
                    concept_name
                )
                
                # Create semantic mapping: Property -> Column
                session.run("""
                    MATCH (p:Property {name: $prop_name, concept: $concept_name})
                    MATCH (col:Column {name: $column_name, table: $table_name})
                    MERGE (p)-[m:MAPS_TO_COLUMN]->(col)
                    SET m.confidence = $confidence,
                        m.connection_id = $connection_id,
                        m.semantic_type = $concept_name,
                        m.last_updated = datetime(),
                        m.meaning = $meaning
                """, prop_name=property_name,
                     concept_name=concept_name,
                     column_name=column_name,
                     table_name=table,
                     confidence=confidence,
                     connection_id=connection_id,
                     meaning=f"{concept_name}.{property_name}")
                
                stats['mappings_created'] += 1
                stats['columns_synced'] += 1
                
                logger.debug(f"📌 Mapped: {concept_name}.{property_name} → {table}.{column_name} (confidence: {confidence:.0%})")
    
    def _calculate_mapping_confidence(
        self,
        property_name: str,
        column_name: str,
        concept_name: str
    ) -> float:
        """Calculate confidence score for property->column mapping"""
        
        property_lower = property_name.lower()
        column_lower = column_name.lower()
        concept_lower = concept_name.lower()
        
        # Exact match = 100%
        if property_lower == column_lower:
            return 1.0
        
        # Property name contained in column = 95%
        if property_lower in column_lower or column_lower in property_lower:
            return 0.95
        
        # Concept + property in column = 90%
        if concept_lower in column_lower and property_lower in column_lower:
            return 0.90
        
        # Concept in column = 85%
        if concept_lower in column_lower:
            return 0.85
        
        # Partial match (first 3 chars) = 75%
        if len(property_lower) >= 3 and property_lower[:3] in column_lower:
            return 0.75
        
        # Default = 70%
        return 0.70
    
    def _create_synonym_index(
        self,
        session,
        concepts: Dict[str, Any],
        connection_id: str
    ):
        """Create synonym index for fuzzy concept matching"""
        
        # Common synonyms for business terms
        synonym_map = {
            'Vendor': ['supplier', 'seller', 'merchant', 'provider'],
            'Product': ['item', 'goods', 'merchandise', 'sku'],
            'Order': ['purchase', 'po', 'requisition'],
            'Customer': ['client', 'buyer', 'purchaser'],
            'Invoice': ['bill', 'receipt', 'statement'],
            'Payment': ['transaction', 'settlement', 'remittance'],
        }
        
        for concept_name in concepts.keys():
            synonyms = synonym_map.get(concept_name, [])
            
            for synonym in synonyms:
                session.run("""
                    MATCH (c:Concept {name: $concept_name, connection: $connection_id})
                    MERGE (s:Synonym {term: $synonym})
                    MERGE (s)-[:REFERS_TO]->(c)
                    SET s.last_updated = datetime()
                """, concept_name=concept_name,
                     connection_id=connection_id,
                     synonym=synonym.lower())
    
    def sync_all_ontologies(self, ontology_dir: str = None) -> Dict[str, Any]:
        """
        Sync all ontology YAML files in a directory
        
        Args:
            ontology_dir: Directory containing ontology files (default: ./ontology/)
            
        Returns:
            Aggregated sync statistics
        """
        if ontology_dir is None:
            ontology_dir = Path(__file__).parent.parent.parent.parent / 'ontology'
        else:
            ontology_dir = Path(ontology_dir)
        
        if not ontology_dir.exists():
            logger.warning(f"Ontology directory not found: {ontology_dir}")
            return {'success': False, 'error': 'Directory not found'}
        
        # Find all ontology YAML files
        ontology_files = list(ontology_dir.glob('*_ontology_*.yml'))
        
        if not ontology_files:
            logger.warning(f"No ontology files found in: {ontology_dir}")
            return {'success': False, 'error': 'No ontology files found'}
        
        logger.info(f"📂 Found {len(ontology_files)} ontology files to sync")
        
        aggregated_stats = {
            'success': True,
            'files_synced': 0,
            'files_failed': 0,
            'total_concepts': 0,
            'total_mappings': 0,
            'total_relationships': 0,
            'errors': []
        }
        
        for ontology_file in ontology_files:
            logger.info(f"🔄 Syncing: {ontology_file.name}")
            
            result = self.sync_ontology_file(str(ontology_file))
            
            if result.get('success'):
                aggregated_stats['files_synced'] += 1
                aggregated_stats['total_concepts'] += result.get('concepts_synced', 0)
                aggregated_stats['total_mappings'] += result.get('mappings_created', 0)
                aggregated_stats['total_relationships'] += result.get('relationships_synced', 0)
            else:
                aggregated_stats['files_failed'] += 1
                aggregated_stats['errors'].append({
                    'file': ontology_file.name,
                    'error': result.get('error')
                })
        
        logger.info(f"✅ Sync complete: {aggregated_stats['files_synced']}/{len(ontology_files)} files synced")
        return aggregated_stats
    
    def get_ontology_enhanced_insights(
        self,
        query: str,
        connection_id: str
    ) -> Dict[str, Any]:
        """
        Get ontology-enhanced insights for a query
        
        This is called by knowledge_graph.py to provide semantic recommendations
        
        Args:
            query: Natural language query
            connection_id: Database connection identifier
            
        Returns:
            Enhanced insights with ontology-based recommendations
        """
        if not self.enabled or not self.driver:
            return {}
        
        try:
            query_lower = query.lower()
            insights = {
                'concepts_detected': [],
                'suggested_columns': {},
                'semantic_mappings': [],
                'recommendations': []
            }
            
            with self.driver.session() as session:
                # 1. Find concepts mentioned in query (including synonyms and properties)
                # Enhanced to match partial property names (e.g., "vendor" matches "vendorname")
                result = session.run("""
                    MATCH (c:Concept {connection: $connection_id})
                    WHERE toLower($user_query) CONTAINS toLower(c.name)
                    RETURN c.name as concept, c.confidence as confidence, c.description as description
                    
                    UNION
                    
                    MATCH (s:Synonym)-[:REFERS_TO]->(c:Concept {connection: $connection_id})
                    WHERE toLower($user_query) CONTAINS toLower(s.term)
                    RETURN c.name as concept, c.confidence as confidence, c.description as description
                    
                    UNION
                    
                    MATCH (c:Concept {connection: $connection_id})-[:HAS_PROPERTY]->(p:Property)
                    WHERE toLower(p.name) CONTAINS toLower($user_query)
                        OR toLower($user_query) CONTAINS toLower(p.name)
                        OR any(word IN split(toLower($user_query), ' ') WHERE toLower(p.name) CONTAINS word AND size(word) > 3)
                    RETURN c.name as concept, c.confidence as confidence, c.description as description
                """, user_query=query_lower, connection_id=connection_id)
                
                concepts_found = []
                for record in result:
                    concept = {
                        'name': record['concept'],
                        'confidence': record['confidence'],
                        'description': record['description']
                    }
                    concepts_found.append(concept)
                    insights['concepts_detected'].append(concept)
                
                # 2. For each concept, get recommended columns via semantic mappings
                # Enhanced with query-relevance scoring
                query_words = [w for w in query_lower.split() if len(w) > 3]  # Filter meaningful words
                
                for concept_data in concepts_found:
                    concept_name = concept_data['name']
                    
                    column_result = session.run("""
                        MATCH (c:Concept {name: $concept_name, connection: $connection_id})
                        MATCH (c)-[:HAS_PROPERTY]->(p:Property)
                        MATCH (p)-[m:MAPS_TO_COLUMN]->(col:Column)
                        MATCH (t:Table)-[:HAS_COLUMN]->(col)
                        RETURN DISTINCT
                            t.name as table_name,
                            col.name as column_name,
                            col.data_type as data_type,
                            p.name as property_name,
                            m.confidence as confidence,
                            m.meaning as meaning
                        ORDER BY m.confidence DESC
                    """, concept_name=concept_name, connection_id=connection_id)
                    
                    for col_record in column_result:
                        table_name = col_record['table_name']
                        column_name = col_record['column_name']
                        property_name = col_record['property_name']
                        
                        # Calculate query relevance score
                        relevance_score = 0.0
                        col_lower = column_name.lower()
                        prop_lower = property_name.lower()
                        
                        for word in query_words:
                            if word in col_lower:
                                relevance_score += 2.0  # Column name match is most relevant
                            if word in prop_lower:
                                relevance_score += 1.5  # Property name match is also relevant
                        
                        # Combine confidence with relevance (relevance is more important for ordering)
                        combined_score = (relevance_score * 100) + col_record['confidence']
                        
                        if table_name not in insights['suggested_columns']:
                            insights['suggested_columns'][table_name] = []
                        
                        column_suggestion = {
                            'column': column_name,
                            'data_type': col_record['data_type'],
                            'property': col_record['property_name'],
                            'confidence': col_record['confidence'],
                            'meaning': col_record['meaning'],
                            'relevance_score': combined_score  # Add relevance for sorting
                        }
                        
                        insights['suggested_columns'][table_name].append(column_suggestion)
                        insights['semantic_mappings'].append({
                            'concept': concept_name,
                            'property': col_record['property_name'],
                            'table': table_name,
                            'column': column_name,
                            'confidence': col_record['confidence']
                        })
                
                # Sort columns by relevance score
                for table in insights['suggested_columns']:
                    insights['suggested_columns'][table].sort(
                        key=lambda x: x.get('relevance_score', 0), 
                        reverse=True
                    )
                    
                    # Log top columns after sorting
                    if insights['suggested_columns'][table]:
                        logger.info(f"🎯 Top columns for {table} after sorting:")
                        for i, col in enumerate(insights['suggested_columns'][table][:5], 1):
                            logger.info(f"   {i}. {col['column']} (relevance: {col.get('relevance_score', 0):.0f})")
                
                # 3. Generate human-readable recommendations
                if insights['concepts_detected']:
                    concept_names = [c['name'] for c in insights['concepts_detected']]
                    insights['recommendations'].append({
                        'type': 'ontology',
                        'message': f"Detected business concepts: {', '.join(concept_names)}"
                    })
                
                if insights['suggested_columns']:
                    for table, columns in insights['suggested_columns'].items():
                        top_cols = [c['column'] for c in columns[:3]]
                        logger.info(f"🎯 Creating recommendation for {table} with: {top_cols}")
                        insights['recommendations'].append({
                            'type': 'semantic_mapping',
                            'message': f"Recommended columns in {table}: {', '.join(top_cols)}"
                        })
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get ontology insights: {e}", exc_info=True)
            return {}


# Global instance
_ontology_kg_sync_service = None


def get_ontology_kg_sync_service(config: Dict[str, Any]) -> OntologyKGSyncService:
    """Get or create global ontology sync service"""
    global _ontology_kg_sync_service
    if _ontology_kg_sync_service is None:
        neo4j_config = config.get('neo4j', {})
        _ontology_kg_sync_service = OntologyKGSyncService(neo4j_config)
    return _ontology_kg_sync_service
