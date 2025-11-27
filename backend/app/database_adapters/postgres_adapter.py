"""
PostgreSQL Database Adapter
Adapter for PostgreSQL databases (existing implementation)
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from .base_adapter import BaseDatabaseAdapter

logger = logging.getLogger(__name__)


class PostgresAdapter(BaseDatabaseAdapter):
    """PostgreSQL database adapter"""
    
    @property
    def database_type(self) -> str:
        return "postgresql"
    
    def get_connection(self):
        """Get PostgreSQL connection"""
        if not self.connection_params:
            raise ValueError("Database connection not configured")
        
        params = self.connection_params
        
        return psycopg2.connect(
            host=params['host'],
            port=params.get('port', 5432),
            database=params['database'],
            user=params['username'],
            password=params['password']
        )
    
    def test_connection(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Test PostgreSQL connection"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get database info
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_database()")
            database = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_user")
            user = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            info = {
                "database": database,
                "user": user,
                "version": version,
                "database_type": self.database_type
            }
            
            return True, "Connection successful", info
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, str(e), None
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get list of all PostgreSQL schemas"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    schema_name,
                    (SELECT COUNT(*) FROM information_schema.tables 
                     WHERE table_schema = s.schema_name AND table_type = 'BASE TABLE') as table_count,
                    (SELECT COUNT(*) FROM information_schema.views 
                     WHERE table_schema = s.schema_name) as view_count
                FROM information_schema.schemata s
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                ORDER BY schema_name
            """)
            schemas = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            result = [dict(schema) for schema in schemas]
            logger.info(f"Found {len(result)} schemas")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get schemas: {e}")
            raise
    
    def get_schema_snapshot(self, schema_name: str) -> Dict[str, Any]:
        """Get PostgreSQL schema snapshot"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (schema_name,))
            tables = cursor.fetchall()
            
            snapshot = {
                'database_name': self.connection_params['database'],
                'schema_name': schema_name,
                'database_type': self.database_type,
                'tables': [],
                'total_tables': len(tables),
                'timestamp': datetime.now().isoformat()
            }
            
            # Process each table
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
                
                snapshot['tables'].append({
                    'schema_name': schema_name,
                    'table_name': table_name,
                    'full_name': f"{schema_name}.{table_name}",
                    'columns': [dict(col) for col in columns]
                })
            
            cursor.close()
            conn.close()
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to get schema snapshot: {e}")
            raise
    
    def get_database_snapshot(self) -> Dict[str, Any]:
        """Get complete PostgreSQL database snapshot"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get all tables from all schemas
            cursor.execute("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                AND table_type = 'BASE TABLE'
                ORDER BY table_schema, table_name
            """)
            tables = cursor.fetchall()
            
            snapshot = {
                'database_name': self.connection_params['database'],
                'database_type': self.database_type,
                'connection_info': {
                    'host': self.connection_params.get('host'),
                    'port': self.connection_params.get('port', 5432),
                    'database': self.connection_params['database']
                },
                'tables': [],
                'total_tables': len(tables),
                'timestamp': datetime.now().isoformat()
            }
            
            # Process tables
            for table in tables:
                table_schema = table['table_schema']
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
                """, (table_schema, table_name))
                columns = cursor.fetchall()
                
                snapshot['tables'].append({
                    'schema_name': table_schema,
                    'table_name': table_name,
                    'full_name': f"{table_schema}.{table_name}",
                    'columns': [dict(col) for col in columns]
                })
            
            cursor.close()
            conn.close()
            
            self.schema_cache = snapshot
            self.cache_timestamp = datetime.now()
            
            logger.info(f"Database snapshot created: {len(tables)} tables")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to get database snapshot: {e}")
            raise
    
    def execute_query(self, sql_query: str) -> Tuple[List[Dict[str, Any]], List[str], float]:
        """Execute PostgreSQL query"""
        import time
        
        try:
            start_time = time.time()
            
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(sql_query)
            
            # Handle SELECT queries
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                results = [
                    {k: self.serialize_value(v) for k, v in dict(row).items()}
                    for row in rows
                ]
            else:
                # Handle INSERT/UPDATE/DELETE
                conn.commit()
                columns = []
                results = []
            
            execution_time = time.time() - start_time
            
            cursor.close()
            conn.close()
            
            logger.info(f"Query executed successfully: {len(results)} rows in {execution_time:.3f}s")
            return results, columns, execution_time
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_table_info(self, schema_name: str, table_name: str) -> Dict[str, Any]:
        """Get detailed PostgreSQL table information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get columns
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema_name, table_name))
            columns = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                'schema_name': schema_name,
                'table_name': table_name,
                'columns': [dict(col) for col in columns]
            }
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            raise
