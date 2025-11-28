"""
Database service for managing multi-database connections and queries
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
import logging
from ..database_adapters.adapter_factory import DatabaseAdapterFactory
from ..models.schemas import DatabaseType

logger = logging.getLogger(__name__)


def serialize_value(value):
    """Convert non-JSON serializable types to JSON serializable types"""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, bytes):
        return value.decode('utf-8', errors='ignore')
    elif value is None:
        return None
    return value


class DatabaseService:
    """Manages database connections and operations using adapter pattern"""
    
    def __init__(self):
        self.connection_params = None
        self.adapter = None
        self.database_type = "postgresql"  # Track current database type
        self.schema_cache = None
        self.cache_timestamp = None
        self.schema_snapshots = {}  # Store snapshots per schema: {schema_name: snapshot_data}
        self.selected_tables = None  # Store user-selected tables for filtering
        
    def set_connection(self, database_type: str = "postgresql",
                      host: Optional[str] = None, 
                      port: Optional[int] = None, 
                      database: Optional[str] = None, 
                      username: Optional[str] = None, 
                      password: Optional[str] = None,
                      sid: Optional[str] = None,
                      service_name: Optional[str] = None,
                      file_path: Optional[str] = None,
                      use_docker: bool = False, 
                      docker_container: Optional[str] = None):
        """Set database connection parameters and initialize appropriate adapter"""
        self.database_type = database_type  # Store database type
        self.connection_params = {
            'database_type': database_type,
            'host': host,
            'port': port,
            'database': database,
            'username': username,
            'password': password,
            'sid': sid,
            'service_name': service_name,
            'file_path': file_path,
            'use_docker': use_docker,
            'docker_container': docker_container
        }
        
        # Create appropriate adapter
        self.adapter = DatabaseAdapterFactory.create_adapter(
            database_type=database_type,
            connection_params={
                'host': host,
                'port': port,
                'database': database,
                'username': username,
                'password': password,
                'sid': sid,
                'service_name': service_name,
                'file_path': file_path
            }
        )
        
        # Clear cache when connection changes
        self.schema_cache = None
        self.cache_timestamp = None
        self.schema_snapshots = {}
    
    def get_database_type(self) -> str:
        """Get current database type"""
        return self.database_type
    
    def set_selected_tables(self, table_names: List[str]):
        """Set the list of tables user wants to work with"""
        self.selected_tables = table_names
        # Clear cache when selection changes
        self.schema_cache = None
        self.cache_timestamp = None
        logger.info(f"Selected tables set: {len(table_names)} tables")
    
    def get_selected_tables(self) -> Optional[List[str]]:
        """Get the list of selected tables"""
        return self.selected_tables
    
    def clear_selected_tables(self):
        """Clear table selection (show all tables)"""
        self.selected_tables = None
        self.schema_cache = None
        self.cache_timestamp = None
        logger.info("Table selection cleared")
        
    def get_connection(self):
        """Get database connection through adapter"""
        if not self.adapter:
            raise ValueError("Database connection not configured")
        return self.adapter.get_connection()
    
    def test_connection(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Test database connection using adapter"""
        if not self.adapter:
            return False, "Database adapter not initialized", None
            
        try:
            success, message, info = self.adapter.test_connection()
            if success:
                return True, message, info
            else:
                return False, message, None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, str(e), None
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get list of all schemas in the database using adapter"""
        if not self.adapter:
            raise ValueError("Database adapter not initialized")
            
        try:
            schemas = self.adapter.get_all_schemas()
            logger.info(f"Found {len(schemas)} schemas")
            return schemas
        except Exception as e:
            logger.error(f"Failed to get schemas: {e}")
            raise
    
    def get_schema_snapshot(self, schema_name: str) -> Dict[str, Any]:
        """Get snapshot for a specific schema using adapter"""
        if not self.adapter:
            raise ValueError("Database adapter not initialized")
            
        try:
            # Check cache
            if schema_name in self.schema_snapshots:
                cached = self.schema_snapshots[schema_name]
                # Cache for 1 hour
                elapsed = (datetime.now() - cached['timestamp']).total_seconds()
                if elapsed < 3600:
                    logger.info(f"Returning cached snapshot for schema: {schema_name}")
                    return cached['data']
            
            # Get schema snapshot from adapter
            snapshot = self.adapter.get_schema_snapshot(schema_name)
            
            # Cache the snapshot
            self.schema_snapshots[schema_name] = {
                'data': snapshot,
                'timestamp': datetime.now()
            }
            
            logger.info(f"Schema snapshot created for {schema_name}: {snapshot.get('total_tables', 0)} tables")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to get schema snapshot for {schema_name}: {e}")
            raise
            
            # Get tables for this schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (schema_name,))
            tables = cursor.fetchall()
            
            # Get views for this schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = %s
                ORDER BY table_name
            """, (schema_name,))
            views = cursor.fetchall()
            
            snapshot = {
                'database_name': self.connection_params['database'],
                'schema_name': schema_name,
                'tables': [],
                'views': [],
                'total_tables': len(tables),
                'total_views': len(views),
                'timestamp': datetime.now().isoformat()
            }
            
            # Process tables
            for table in tables:
                table_name = table['table_name']
                
                # Get columns
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema_name, table_name))
                columns = cursor.fetchall()
                
                # Get primary keys
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.key_column_usage
                    WHERE table_schema = %s AND table_name = %s
                    AND constraint_name IN (
                        SELECT constraint_name
                        FROM information_schema.table_constraints
                        WHERE table_schema = %s AND table_name = %s
                        AND constraint_type = 'PRIMARY KEY'
                    )
                """, (schema_name, table_name, schema_name, table_name))
                pk_columns = [row['column_name'] for row in cursor.fetchall()]
                
                # Mark primary key columns
                columns_list = []
                for col in columns:
                    col_dict = dict(col)
                    col_dict['primary_key'] = col_dict['column_name'] in pk_columns
                    columns_list.append(col_dict)
                
                # Get sample data (first 3 rows)
                try:
                    cursor.execute(f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT 3')
                    sample_data = cursor.fetchall()
                except Exception as e:
                    logger.warning(f"Could not fetch sample data from {schema_name}.{table_name}: {e}")
                    sample_data = []
                
                snapshot['tables'].append({
                    'schema_name': schema_name,
                    'table_name': table_name,
                    'full_name': f"{schema_name}.{table_name}",
                    'columns': columns_list,
                    'sample_data': [dict(row) for row in sample_data]
                })
            
            # Process views
            for view in views:
                view_name = view['table_name']
                
                # Get columns for view
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema_name, view_name))
                columns = cursor.fetchall()
                
                # Get view definition
                cursor.execute("""
                    SELECT definition 
                    FROM pg_views 
                    WHERE schemaname = %s AND viewname = %s
                """, (schema_name, view_name))
                view_def = cursor.fetchone()
                view_definition = view_def['definition'] if view_def else None
                
                snapshot['views'].append({
                    'schema_name': schema_name,
                    'view_name': view_name,
                    'full_name': f"{schema_name}.{view_name}",
                    'columns': [dict(col) for col in columns],
                    'definition': view_definition
                })
            
            cursor.close()
            conn.close()
            
            # Cache the result
            self.schema_snapshots[schema_name] = {
                'data': snapshot,
                'timestamp': datetime.now()
            }
            
            logger.info(f"Schema snapshot created for '{schema_name}': {len(tables)} tables, {len(views)} views")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to get schema snapshot for '{schema_name}': {e}")
            raise
    
    def get_database_snapshot(self) -> Dict[str, Any]:
        """Get complete database schema snapshot including tables and views"""
        if not self.adapter:
            raise ValueError("Database adapter not initialized")
            
        try:
            # Check cache (simple time-based cache)
            if self.schema_cache and self.cache_timestamp:
                # Cache for 1 hour
                elapsed = (datetime.now() - self.cache_timestamp).total_seconds()
                if elapsed < 3600:
                    logger.info("Returning cached schema")
                    return self.schema_cache
            
            # Get snapshot from adapter
            snapshot = self.adapter.get_database_snapshot()
            
            # Filter by selected tables if user has made a selection
            if self.selected_tables is not None:
                logger.info(f"Filtering snapshot to {len(self.selected_tables)} selected tables")
                filtered_tables = []
                
                for table in snapshot.get('tables', []):
                    # Check both table_name and full_name (schema.table)
                    table_name = table.get('table_name', '')
                    full_name = table.get('full_name', '')
                    
                    if table_name in self.selected_tables or full_name in self.selected_tables:
                        filtered_tables.append(table)
                
                snapshot['tables'] = filtered_tables
                snapshot['total_tables'] = len(filtered_tables)
                logger.info(f"Filtered snapshot: {len(filtered_tables)} tables out of {snapshot.get('total_tables', 0)}")
            
            # Cache the result
            self.schema_cache = snapshot
            self.cache_timestamp = datetime.now()
            
            logger.info(f"Database snapshot created: {snapshot.get('total_tables', 0)} tables")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to get database snapshot: {e}")
            raise
    
    def execute_query(self, sql_query: str) -> Tuple[List[Dict[str, Any]], List[str], float]:
        """Execute SQL query and return results using adapter"""
        if not self.adapter:
            raise ValueError("Database adapter not initialized")
            
        try:
            results, columns, execution_time = self.adapter.execute_query(sql_query)
            logger.info(f"Query executed successfully: {len(results)} rows in {execution_time:.3f}s")
            return results, columns, execution_time
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_schema_context(self, include_samples: bool = False) -> str:
        """Get formatted schema context for LLM (optimized for token usage)"""
        snapshot = self.get_database_snapshot()
        
        # Use compact format to reduce tokens
        context = f"Database: {snapshot['database_name']}\n"
        context += f"Tables: {snapshot['total_tables']}, Views: {snapshot.get('total_views', 0)}\n\n"
        
        # Include tables
        context += "TABLES:\n"
        for table in snapshot['tables']:
            # Use full_name if available (includes schema), otherwise just table_name
            table_name = table.get('full_name') or table.get('table_name')
            
            # Compact table format: Table(columns)
            cols = []
            for col in table['columns']:
                # Only include essential info: name and type
                col_str = f"{col['column_name']}:{col['data_type']}"
                cols.append(col_str)
            
            context += f"{table_name}({', '.join(cols)})\n"
            
            # Only include sample data if explicitly requested and limit to 1 row
            if include_samples and table.get('sample_data') and len(table['sample_data']) > 0:
                # Show only first row as example
                sample = table['sample_data'][0]
                # Limit sample data to first 3 columns to save tokens
                limited_sample = {k: v for i, (k, v) in enumerate(sample.items()) if i < 3}
                context += f"  Sample: {limited_sample}\n"
        
        # Include views
        if snapshot.get('views'):
            context += "\nVIEWS:\n"
            for view in snapshot['views']:
                # Use full_name if available (includes schema), otherwise just view_name
                view_name = view.get('full_name') or view.get('view_name')
                
                cols = []
                for col in view['columns']:
                    col_str = f"{col['column_name']}:{col['data_type']}"
                    cols.append(col_str)
                context += f"{view_name}({', '.join(cols)})\n"
        
        return context
    
    def get_relevant_tables_context(self, question: str, max_tables: int = 10) -> str:
        """Get context for only relevant tables/views based on the question (further optimization)"""
        snapshot = self.get_database_snapshot()
        
        # Simple keyword matching to find relevant tables
        question_lower = question.lower()
        keywords = question_lower.split()
        
        # Score tables based on name matching
        scored_tables = []
        for table in snapshot['tables']:
            table_name = (table.get('table_name') or '').lower()
            full_name = (table.get('full_name') or table_name).lower()
            score = 0
            
            # Check if table name appears in question
            if table_name in question_lower or full_name in question_lower:
                score += 10
            
            # Check if any keyword matches table name
            for keyword in keywords:
                if keyword in table_name or table_name in keyword:
                    score += 2
                if keyword in full_name or full_name in keyword:
                    score += 2
                    score += 5
            
            # Check column names
            for col in table['columns']:
                col_name = col['column_name'].lower()
                if col_name in question_lower:
                    score += 3
                for keyword in keywords:
                    if keyword in col_name:
                        score += 1
            
            scored_tables.append((score, 'table', table))
        
        # Score views similarly
        for view in snapshot.get('views', []):
            view_name = view['view_name'].lower()
            score = 0
            
            if view_name in question_lower:
                score += 10
            
            for keyword in keywords:
                if keyword in view_name or view_name in keyword:
                    score += 5
            
            for col in view['columns']:
                col_name = col['column_name'].lower()
                if col_name in question_lower:
                    score += 3
                for keyword in keywords:
                    if keyword in col_name:
                        score += 1
            
            scored_tables.append((score, 'view', view))
        
        # Sort by score and take top N tables/views
        scored_tables.sort(reverse=True, key=lambda x: x[0])
        relevant_items = [(item_type, item) for s, item_type, item in scored_tables[:max_tables] if s > 0]
        
        # If no relevant items found, return all tables (but limited)
        if not relevant_items:
            relevant_items = [('table', t) for t in snapshot['tables'][:max_tables]]
        
        # Build detailed context with clear column information
        context = f"Database: {snapshot['database_name']}\n"
        context += f"Relevant tables/views for your question:\n\n"
        
        for item_type, item in relevant_items:
            if item_type == 'table':
                context += f"Table: {item['table_name']}\n"
                context += "Columns:\n"
                for col in item['columns']:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    context += f"  - {col['column_name']} ({col['data_type']}) {nullable}{default}\n"
                context += "\n"
            else:  # view
                context += f"View: {item['view_name']}\n"
                context += "Columns:\n"
                for col in item['columns']:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    context += f"  - {col['column_name']} ({col['data_type']}) {nullable}\n"
                context += "\n"
        
        return context


# Global database service instance
db_service = DatabaseService()
