"""
Neo4j Knowledge Graph Service
Builds and queries a knowledge graph representation of database schema
for enhanced SQL agent understanding
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
import networkx as nx

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Service for managing Neo4j knowledge graph of database schema"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize knowledge graph service
        
        Args:
            config: Configuration dictionary with neo4j settings
        """
        self.config = config
        self.neo4j_config = config.get('neo4j', {})
        self.enabled = self.neo4j_config.get('enabled', False)
        self.driver = None
        self._local_graph = nx.DiGraph()  # Fallback local graph
        
        if self.enabled:
            self._connect()
    
    def _connect(self):
        """Establish connection to Neo4j with timeout"""
        try:
            uri = self.neo4j_config.get('uri', 'bolt://localhost:7687')
            username = self.neo4j_config.get('username', 'neo4j')
            password = self.neo4j_config.get('password', 'password')
            
            # Create driver with connection timeout
            self.driver = GraphDatabase.driver(
                uri, 
                auth=(username, password),
                connection_timeout=5.0,  # 5 second connection timeout
                max_connection_lifetime=300  # 5 minute max connection lifetime
            )
            # Test connection with timeout
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Successfully connected to Neo4j at {uri}")
            
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.enabled = False
            self.driver = None
        except Exception as e:
            logger.error(f"Neo4j connection error: {e}")
            self.enabled = False
            self.driver = None
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def test_connection(self, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Test Neo4j connection with timeout
        
        Args:
            timeout: Maximum time to wait for connection test (seconds)
        
        Returns:
            Dictionary with connection status and info
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "Neo4j knowledge graph is disabled in configuration"
            }
        
        import concurrent.futures
        
        def _test():
            try:
                with self.driver.session() as session:
                    result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions")
                    record = result.single()
                    return {
                        "status": "connected",
                        "message": "Successfully connected to Neo4j",
                        "version": record["versions"][0] if record else "unknown"
                    }
            except Exception as e:
                logger.error(f"Connection test failed: {e}")
                return {
                    "status": "error",
                    "message": f"Connection failed: {str(e)}"
                }
        
        # Run test with timeout in separate thread
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_test)
                return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            logger.error(f"Neo4j connection test timed out after {timeout} seconds")
            return {
                "status": "timeout",
                "message": f"Connection test timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            return {
                "status": "error",
                "message": f"Test failed: {str(e)}"
            }
    
    def clear_graph(self):
        """Clear all nodes and relationships from the graph"""
        if not self.enabled or not self.driver:
            self._local_graph.clear()
            return
        
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            logger.info("Knowledge graph cleared")
        except Exception as e:
            logger.error(f"Failed to clear graph: {e}")
            raise
    
    def build_from_schema(self, schema_snapshot: Dict[str, Any]):
        """
        Build knowledge graph from database schema snapshot
        
        Args:
            schema_snapshot: Database schema information
        """
        if not self.enabled:
            self._build_local_graph(schema_snapshot)
            return
        
        try:
            with self.driver.session() as session:
                # Create database node - use 'database_name' field
                db_name = schema_snapshot.get('database_name', schema_snapshot.get('database', 'unknown'))
                session.run("""
                    MERGE (db:Database {name: $db_name})
                    SET db.total_tables = $total_tables,
                        db.last_updated = datetime()
                """, db_name=db_name,
                     total_tables=len(schema_snapshot.get('tables', [])))
                
                # Process each table (they now include schema_name)
                for table_info in schema_snapshot.get('tables', []):
                    # Extract schema name from table info or use 'public' as default
                    schema_name = table_info.get('schema_name', 'public')
                    table_name = table_info['table_name']
                    columns = table_info.get('columns', [])
                    
                    # Create schema node if not exists
                    session.run("""
                        MATCH (db:Database {name: $db_name})
                        MERGE (s:Schema {name: $schema_name})
                        MERGE (db)-[:HAS_SCHEMA]->(s)
                    """, db_name=db_name, schema_name=schema_name)
                    
                    # Create table node
                    session.run("""
                        MATCH (s:Schema {name: $schema_name})
                        MERGE (t:Table {name: $table_name, schema: $schema_name})
                        SET t.row_count = $row_count,
                            t.column_count = $column_count,
                            t.description = $description
                        MERGE (s)-[:CONTAINS]->(t)
                    """, schema_name=schema_name,
                         table_name=table_name,
                         row_count=table_info.get('row_count', 0),
                         column_count=len(columns),
                         description=table_info.get('description', ''))
                    
                    # Create column nodes
                    for col in columns:
                        # Handle is_nullable which could be 'YES', 'NO', or boolean
                        is_nullable_raw = col.get('is_nullable', 'YES')
                        is_nullable = is_nullable_raw == 'YES' if isinstance(is_nullable_raw, str) else bool(is_nullable_raw)
                        
                        session.run("""
                            MATCH (t:Table {name: $table_name, schema: $schema_name})
                            MERGE (c:Column {name: $col_name, table: $table_name, schema: $schema_name})
                            SET c.data_type = $data_type,
                                c.is_nullable = $is_nullable,
                                c.default_value = $default_val
                            MERGE (t)-[:HAS_COLUMN]->(c)
                        """, schema_name=schema_name,
                             table_name=table_name,
                             col_name=col.get('column_name', col.get('name', 'unknown')),
                             data_type=col.get('data_type', 'unknown'),
                             is_nullable=is_nullable,
                             default_val=str(col.get('column_default', col.get('default_value', ''))) if col.get('column_default') or col.get('default_value') else '')
                    
                    # Create foreign key relationships (if they exist in the snapshot)
                    for fk in table_info.get('foreign_keys', []):
                        try:
                            session.run("""
                                MATCH (t1:Table {name: $table_name, schema: $schema_name})
                                MATCH (t2:Table {name: $ref_table, schema: $schema_name})
                                MATCH (c1:Column {name: $col_name, table: $table_name, schema: $schema_name})
                                MATCH (c2:Column {name: $ref_col, table: $ref_table, schema: $schema_name})
                                MERGE (c1)-[r:REFERENCES]->(c2)
                                SET r.constraint_name = $fk_name
                                MERGE (t1)-[:RELATED_TO]->(t2)
                            """, schema_name=schema_name,
                                 table_name=table_name,
                                 ref_table=fk['referenced_table'],
                                 col_name=fk['column_name'],
                                 ref_col=fk['referenced_column'],
                                 fk_name=fk.get('constraint_name', ''))
                        except Exception as fk_error:
                            logger.warning(f"Failed to create FK relationship: {fk_error}")
                
                # Create indexes (if they exist in the snapshot)
                for table_info in schema_snapshot.get('tables', []):
                    schema_name = table_info.get('schema_name', 'public')
                    for idx in table_info.get('indexes', []):
                        try:
                            session.run("""
                                MATCH (t:Table {name: $table_name, schema: $schema_name})
                                MERGE (i:Index {name: $idx_name})
                                SET i.is_unique = $is_unique,
                                    i.columns = $columns
                                MERGE (t)-[:HAS_INDEX]->(i)
                            """, schema_name=schema_name,
                                 table_name=table_info['table_name'],
                                 idx_name=idx['index_name'],
                                 is_unique=idx.get('is_unique', False),
                                 columns=idx.get('columns', []))
                        except Exception as idx_error:
                            logger.warning(f"Failed to create index: {idx_error}")
                
                logger.info(f"✅ Knowledge graph built with {len(schema_snapshot.get('tables', []))} tables")
                
        except Exception as e:
            logger.error(f"❌ Failed to build knowledge graph: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback to local graph
            self._build_local_graph(schema_snapshot)
                
        except Exception as e:
            logger.error(f"Failed to build knowledge graph: {e}")
            # Fallback to local graph
            self._build_local_graph(schema_snapshot)
    
    def _build_local_graph(self, schema_snapshot: Dict[str, Any]):
        """Build local NetworkX graph as fallback"""
        self._local_graph.clear()
        
        for table_info in schema_snapshot.get('tables', []):
            table_name = table_info['table_name']
            self._local_graph.add_node(table_name, 
                                      node_type='table',
                                      row_count=table_info.get('row_count', 0),
                                      columns=len(table_info.get('columns', [])))
            
            # Add foreign key relationships
            for fk in table_info.get('foreign_keys', []):
                ref_table = fk['referenced_table']
                self._local_graph.add_edge(table_name, ref_table, 
                                          edge_type='foreign_key',
                                          column=fk['column_name'],
                                          ref_column=fk['referenced_column'])
        
        logger.info(f"Local graph built with {self._local_graph.number_of_nodes()} tables")
    
    def get_table_relationships(self, table_name: str, max_depth: int = 2) -> Dict[str, Any]:
        """
        Get relationships for a specific table
        
        Args:
            table_name: Name of the table
            max_depth: Maximum depth to traverse relationships
            
        Returns:
            Dictionary with related tables and relationship information
        """
        if not self.enabled:
            return self._get_local_table_relationships(table_name, max_depth)
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH path = (t1:Table {name: $table_name})-[r:RELATED_TO*1..$depth]-(t2:Table)
                    RETURN t1.name as source, t2.name as target, 
                           length(path) as distance,
                           [rel in relationships(path) | type(rel)] as relationship_types
                    ORDER BY distance
                """, table_name=table_name, depth=max_depth)
                
                relationships = []
                for record in result:
                    relationships.append({
                        'source': record['source'],
                        'target': record['target'],
                        'distance': record['distance'],
                        'relationship_types': record['relationship_types']
                    })
                
                return {
                    'table': table_name,
                    'related_tables': [r['target'] for r in relationships],
                    'relationships': relationships
                }
                
        except Exception as e:
            logger.error(f"Failed to get table relationships: {e}")
            return self._get_local_table_relationships(table_name, max_depth)
    
    def _get_local_table_relationships(self, table_name: str, max_depth: int = 2) -> Dict[str, Any]:
        """Get table relationships from local graph"""
        if table_name not in self._local_graph:
            return {'table': table_name, 'related_tables': [], 'relationships': []}
        
        try:
            # Find all tables within max_depth
            related = []
            for target in self._local_graph.nodes():
                if target != table_name:
                    try:
                        path_length = nx.shortest_path_length(self._local_graph, table_name, target)
                        if path_length <= max_depth:
                            related.append({
                                'source': table_name,
                                'target': target,
                                'distance': path_length
                            })
                    except nx.NetworkXNoPath:
                        continue
            
            return {
                'table': table_name,
                'related_tables': [r['target'] for r in related],
                'relationships': related
            }
        except Exception as e:
            logger.error(f"Local graph query failed: {e}")
            return {'table': table_name, 'related_tables': [], 'relationships': []}
    
    def find_join_path(self, table1: str, table2: str) -> Optional[List[str]]:
        """
        Find the shortest join path between two tables
        
        Args:
            table1: First table name
            table2: Second table name
            
        Returns:
            List of table names forming the join path, or None if no path exists
        """
        if not self.enabled:
            return self._find_local_join_path(table1, table2)
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH path = shortestPath((t1:Table {name: $table1})-[:RELATED_TO*]-(t2:Table {name: $table2}))
                    RETURN [node in nodes(path) | node.name] as path
                """, table1=table1, table2=table2)
                
                record = result.single()
                if record:
                    return record['path']
                return None
                
        except Exception as e:
            logger.error(f"Failed to find join path: {e}")
            return self._find_local_join_path(table1, table2)
    
    def _find_local_join_path(self, table1: str, table2: str) -> Optional[List[str]]:
        """Find join path in local graph"""
        try:
            if table1 in self._local_graph and table2 in self._local_graph:
                return nx.shortest_path(self._local_graph.to_undirected(), table1, table2)
            return None
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def get_related_tables_for_query(self, mentioned_tables: List[str]) -> Dict[str, Any]:
        """
        Get all tables related to the mentioned tables that might be relevant for a query
        
        Args:
            mentioned_tables: List of table names mentioned in the user query
            
        Returns:
            Dictionary with related tables and suggested joins
        """
        all_related = set(mentioned_tables)
        suggested_joins = []
        
        # Get relationships for each mentioned table
        for table in mentioned_tables:
            relationships = self.get_table_relationships(table, max_depth=2)
            all_related.update(relationships.get('related_tables', []))
        
        # Find join paths between mentioned tables
        for i, table1 in enumerate(mentioned_tables):
            for table2 in mentioned_tables[i+1:]:
                path = self.find_join_path(table1, table2)
                if path and len(path) > 2:  # Only suggest if there are intermediate tables
                    suggested_joins.append({
                        'from': table1,
                        'to': table2,
                        'path': path
                    })
        
        return {
            'mentioned_tables': mentioned_tables,
            'related_tables': list(all_related - set(mentioned_tables)),
            'suggested_joins': suggested_joins
        }
    
    def get_graph_insights(self, query: str, schema_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get knowledge graph insights for a natural language query
        
        ENHANCED: Now integrates ontology-based semantic mappings
        
        Args:
            query: User's natural language query
            schema_snapshot: Current database schema snapshot
            
        Returns:
            Dictionary with graph insights including related tables and join suggestions
        """
        insights = {
            'enabled': self.enabled,
            'related_tables': [],
            'suggested_joins': [],
            'table_metadata': {},
            'recommendations': [],
            'suggested_columns': {}  # NEW: Ontology-based column suggestions
        }
        
        if not self.enabled and self._local_graph.number_of_nodes() == 0:
            return insights
        
        # NEW: Get ontology-enhanced insights if available
        try:
            from backend.app.services.ontology_kg_sync import get_ontology_kg_sync_service
            
            # Build proper connection_id that matches ontology file format
            # Format: {database}_{host}_{port}
            # Example: testing_10.35.118.246_5432
            database_name = schema_snapshot.get('database_name', 'unknown')
            
            # Try to get connection details from schema or config
            # Priority: schema metadata > database service config
            if 'connection_info' in schema_snapshot:
                # If schema includes connection info
                conn_info = schema_snapshot['connection_info']
                host = conn_info.get('host', 'localhost')
                port = conn_info.get('port', '5432')
            else:
                # Fallback to database config
                db_config = self.config.get('database', {})
                host = db_config.get('host', 'localhost')
                port = db_config.get('port', 5432)
            
            # Build connection_id matching ontology format
            connection_id = f"{database_name}_{host}_{port}"
            logger.info(f"🔍 Querying Knowledge Graph with connection_id: {connection_id}")
            
            ontology_sync = get_ontology_kg_sync_service(self.config)
            if ontology_sync.enabled:
                ontology_insights = ontology_sync.get_ontology_enhanced_insights(query, connection_id)
                
                # Merge ontology insights
                if ontology_insights:
                    insights['suggested_columns'] = ontology_insights.get('suggested_columns', {})
                    insights['recommendations'].extend(ontology_insights.get('recommendations', []))
                    
                    # Log semantic mappings found
                    semantic_mappings = ontology_insights.get('semantic_mappings', [])
                    if semantic_mappings:
                        logger.info(f"🧠 Found {len(semantic_mappings)} semantic mappings from ontology")
                        logger.info(f"📊 Connection ID matched: {connection_id}")
        except Exception as e:
            logger.warning(f"Ontology integration error: {e}", exc_info=True)
        
        # Extract potential table names from query
        query_lower = query.lower()
        mentioned_tables = []
        
        # ENHANCED: Also search for columns mentioned in the query
        mentioned_columns = {}  # table -> [columns]
        
        # Handle both dict and list formats for schema_snapshot
        tables_data = schema_snapshot.get('tables', {})
        if isinstance(tables_data, dict):
            # Dict format: {'table_name': {table_info}}
            tables_list = [{'table_name': name, **info} for name, info in tables_data.items()]
        else:
            # List format: [{'table_name': 'xxx', ...}]
            tables_list = tables_data
        
        for table_info in tables_list:
            table_name = table_info.get('table_name') or table_info.get('name', '')
            if not table_name:
                continue
                
            if table_name.lower() in query_lower:
                mentioned_tables.append(table_name)
            
            # Check if column names appear in query
            columns_list = table_info.get('columns', [])
            for column in columns_list:
                col_name = column.get('column_name') or column.get('name', '')
                if not col_name:
                    continue
                    
                # More lenient matching: check if column name or parts of it appear
                col_parts = col_name.lower().replace('_', ' ').split()
                if any(part in query_lower for part in col_parts if len(part) > 3):
                    if table_name not in mentioned_columns:
                        mentioned_columns[table_name] = []
                    mentioned_columns[table_name].append({
                        'name': col_name,
                        'type': column.get('data_type') or column.get('type', 'unknown'),
                        'semantic_match': True
                    })
        
        # ENHANCED: Merge ontology suggestions with text-based column detection
        # Prioritize ontology suggestions (higher confidence)
        if insights.get('suggested_columns'):
            for table, ont_cols in insights['suggested_columns'].items():
                if table not in mentioned_columns:
                    mentioned_columns[table] = []
                
                # Convert ontology format to standard format
                for col_info in ont_cols:
                    mentioned_columns[table].append({
                        'name': col_info['column'],
                        'type': col_info.get('data_type', 'unknown'),
                        'semantic_match': True,
                        'ontology_based': True,
                        'confidence': col_info.get('confidence', 0.9),
                        'meaning': col_info.get('meaning', '')
                    })
        
        # Update insights with final column suggestions
        if mentioned_columns:
            insights['suggested_columns'] = mentioned_columns
            col_suggestions = []
            for table, cols in mentioned_columns.items():
                # Sort by confidence if available
                cols_sorted = sorted(cols, key=lambda c: c.get('confidence', 0.7), reverse=True)
                col_names = [c['name'] for c in cols_sorted[:3]]
                col_suggestions.append(f"{table}: {', '.join(col_names)}")
            
            # Create detailed recommendation
            ont_count = sum(1 for cols in mentioned_columns.values() for c in cols if c.get('ontology_based'))
            text_count = sum(1 for cols in mentioned_columns.values() for c in cols if not c.get('ontology_based'))
            
            rec_message = f"Found {len(col_suggestions)} table(s) with relevant columns"
            if ont_count > 0:
                rec_message += f" ({ont_count} from ontology"
                if text_count > 0:
                    rec_message += f", {text_count} from text matching"
                rec_message += ")"
            
            insights['recommendations'].append({
                'type': 'column_match',
                'message': rec_message,
                'details': col_suggestions
            })
        
        if not mentioned_tables:
            # If no tables mentioned directly, try to infer from ontology
            if insights.get('suggested_columns'):
                mentioned_tables = list(insights['suggested_columns'].keys())
                logger.info(f"📊 Inferred tables from ontology: {mentioned_tables}")
            else:
                return insights
        
        # Get related tables and join suggestions
        related_info = self.get_related_tables_for_query(mentioned_tables)
        insights['related_tables'] = related_info['related_tables']
        insights['suggested_joins'] = related_info['suggested_joins']
        
        # Add recommendations based on graph analysis
        if insights['suggested_joins']:
            insights['recommendations'].append({
                'type': 'join_path',
                'message': f"Consider using intermediate tables for joins: {', '.join([sj['path'][1:-1] for sj in insights['suggested_joins'] if len(sj['path']) > 2])}"
            })
        
        if insights['related_tables']:
            insights['recommendations'].append({
                'type': 'related_tables',
                'message': f"Related tables that might be relevant: {', '.join(insights['related_tables'][:5])}"
            })
        
        return insights
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph
        
        Returns:
            Dictionary with graph statistics
        """
        if not self.enabled:
            return {
                'enabled': False,
                'nodes': self._local_graph.number_of_nodes(),
                'edges': self._local_graph.number_of_edges(),
                'using': 'local_graph'
            }
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (n)
                    OPTIONAL MATCH ()-[r]->()
                    RETURN 
                        count(DISTINCT n) as node_count,
                        count(DISTINCT r) as relationship_count,
                        count(DISTINCT CASE WHEN n:Table THEN n END) as table_count,
                        count(DISTINCT CASE WHEN n:Column THEN n END) as column_count
                """)
                
                record = result.single()
                return {
                    'enabled': True,
                    'nodes': record['node_count'],
                    'relationships': record['relationship_count'],
                    'tables': record['table_count'],
                    'columns': record['column_count'],
                    'using': 'neo4j'
                }
        except Exception as e:
            logger.error(f"Failed to get graph statistics: {e}")
            return {
                'enabled': False,
                'error': str(e)
            }


# Global knowledge graph service instance
knowledge_graph_service = None


def get_knowledge_graph_service(config: Dict[str, Any]) -> KnowledgeGraphService:
    """Get or create global knowledge graph service instance"""
    global knowledge_graph_service
    if knowledge_graph_service is None:
        knowledge_graph_service = KnowledgeGraphService(config)
    return knowledge_graph_service
