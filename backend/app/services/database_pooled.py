"""
Enhanced Database Service with Connection Pooling
Replaces direct connections with pooled connections for better performance
"""
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
import logging

from .connection_pool import pool_manager
from .session_manager import session_manager

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


class PooledDatabaseService:
    """
    Database service using connection pooling
    Supports multi-tenant access with session management
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize database service with optional session
        
        Args:
            session_id: Session ID for multi-user support
        """
        self.session_id = session_id
        self.connection_params = None
        self.schema_cache = None
        self.cache_timestamp = None
    
    def set_connection(self, host: str, port: int, database: str, 
                      username: str, password: str,
                      use_docker: bool = False,
                      docker_container: Optional[str] = None) -> str:
        """
        Set database connection parameters and create/get session
        
        Returns:
            session_id: Session identifier for future requests
        """
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'username': username,
            'password': password,
            'use_docker': use_docker,
            'docker_container': docker_container
        }
        
        # Create or get session
        self.session_id = session_manager.get_or_create_session(
            session_id=self.session_id,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password
        )
        
        # Clear cache when connection changes
        self.schema_cache = None
        self.cache_timestamp = None
        
        logger.info(f"Connection configured for session {self.session_id}")
        return self.session_id
    
    def get_connection(self):
        """
        Get a pooled database connection
        Must be returned using return_connection()
        """
        if not self.connection_params:
            raise ValueError("Database connection not configured")
        
        params = self.connection_params
        
        try:
            # Get connection from pool
            conn = pool_manager.get_connection(
                host=params['host'],
                port=params['port'],
                database=params['database'],
                user=params['username'],
                password=params['password']
            )
            return conn
            
        except Exception as e:
            logger.error(f"Failed to get pooled connection: {e}")
            raise
    
    def return_connection(self, conn):
        """Return connection to pool"""
        if not self.connection_params:
            return
        
        params = self.connection_params
        
        try:
            pool_manager.return_connection(
                host=params['host'],
                port=params['port'],
                database=params['database'],
                user=params['username'],
                conn=conn
            )
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")
            # If return fails, close connection
            try:
                conn.close()
            except:
                pass
    
    def execute_with_pool(self, operation_func, *args, **kwargs):
        """
        Execute a database operation with automatic connection management
        
        Args:
            operation_func: Function that accepts (conn, cursor, *args, **kwargs)
        
        Returns:
            Result from operation_func
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            result = operation_func(conn, cursor, *args, **kwargs)
            
            cursor.close()
            self.return_connection(conn)
            
            return result
            
        except Exception as e:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if conn:
                try:
                    self.return_connection(conn)
                except:
                    # If return fails, close connection
                    try:
                        conn.close()
                    except:
                        pass
            raise
    
    def test_connection(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Test database connection using pool"""
        def _test(conn, cursor):
            # Get database info
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
            table_count = cursor.fetchone()[0]
            
            info = {
                'version': version,
                'database': db_name,
                'table_count': table_count
            }
            
            return True, "Connection successful", info
        
        try:
            return self.execute_with_pool(_test)
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, str(e), None
    
    def get_database_snapshot(self) -> Dict[str, Any]:
        """Get complete database schema snapshot using cached session data"""
        # Try to get from session cache first
        if self.session_id:
            session = session_manager.get_session(self.session_id)
            if session and session.schema_cache:
                # Check if cache is still fresh (< 1 hour)
                if session.schema_cache_time:
                    elapsed = (datetime.now() - session.schema_cache_time).total_seconds()
                    if elapsed < 3600:  # 1 hour
                        logger.info("Returning cached schema from session")
                        return session.schema_cache
        
        # Check instance cache
        if self.schema_cache and self.cache_timestamp:
            elapsed = (datetime.now() - self.cache_timestamp).total_seconds()
            if elapsed < 3600:
                logger.info("Returning cached schema from instance")
                return self.schema_cache
        
        # Fetch new snapshot
        def _get_snapshot(conn, cursor):
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            
            snapshot = {
                'database_name': self.connection_params['database'],
                'tables': [],
                'total_tables': len(tables),
                'timestamp': datetime.now().isoformat()
            }
            
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
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cursor.fetchall()
                
                # Get sample data (first 3 rows)
                try:
                    cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 3')
                    sample_data = cursor.fetchall()
                except Exception as e:
                    logger.warning(f"Could not fetch sample data from {table_name}: {e}")
                    sample_data = []
                
                snapshot['tables'].append({
                    'table_name': table_name,
                    'columns': [dict(col) for col in columns],
                    'sample_data': [dict(row) for row in sample_data]
                })
            
            return snapshot
        
        try:
            snapshot = self.execute_with_pool(_get_snapshot)
            
            # Cache in instance
            self.schema_cache = snapshot
            self.cache_timestamp = datetime.now()
            
            # Cache in session
            if self.session_id:
                session = session_manager.get_session(self.session_id)
                if session:
                    session.schema_cache = snapshot
                    session.schema_cache_time = datetime.now()
            
            logger.info(f"Database snapshot created: {len(snapshot['tables'])} tables")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to get database snapshot: {e}")
            raise
    
    def execute_query(self, sql_query: str) -> Tuple[List[Dict[str, Any]], List[str], float]:
        """Execute SQL query and return results using pooled connection"""
        def _execute(conn, cursor):
            import time
            start_time = time.time()
            
            cursor.execute(sql_query)
            
            # Get results
            if cursor.description:
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                results_list = [dict(row) for row in results]
            else:
                results_list = []
                columns = []
            
            execution_time = time.time() - start_time
            
            logger.info(f"Query executed successfully: {len(results_list)} rows in {execution_time:.3f}s")
            return results_list, columns, execution_time
        
        try:
            return self.execute_with_pool(_execute)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_schema_context(self, include_samples: bool = False) -> str:
        """Get formatted schema context for LLM (optimized for token usage)"""
        snapshot = self.get_database_snapshot()
        
        # Use compact format to reduce tokens
        context = f"Database: {snapshot['database_name']}\nTables: {snapshot['total_tables']}\n\n"
        
        for table in snapshot['tables']:
            # Compact table format: Table(columns)
            cols = []
            for col in table['columns']:
                # Only include essential info: name and type
                col_str = f"{col['column_name']}:{col['data_type']}"
                cols.append(col_str)
            
            context += f"{table['table_name']}({', '.join(cols)})\n"
            
            # Only include sample data if explicitly requested and limit to 1 row
            if include_samples and table['sample_data'] and len(table['sample_data']) > 0:
                # Show only first row as example
                sample = table['sample_data'][0]
                # Limit sample data to first 3 columns to save tokens
                limited_sample = {k: v for i, (k, v) in enumerate(sample.items()) if i < 3}
                context += f"  Sample: {limited_sample}\n"
        
        return context
    
    def get_relevant_tables_context(self, question: str, max_tables: int = 10) -> str:
        """Get context for only relevant tables based on the question (further optimization)"""
        snapshot = self.get_database_snapshot()
        
        # Simple keyword matching to find relevant tables
        question_lower = question.lower()
        keywords = question_lower.split()
        
        # Score tables based on name matching
        scored_tables = []
        for table in snapshot['tables']:
            table_name = table['table_name'].lower()
            score = 0
            
            # Check if table name appears in question
            if table_name in question_lower:
                score += 10
            
            # Check if any keyword matches table name
            for keyword in keywords:
                if keyword in table_name or table_name in keyword:
                    score += 5
            
            # Check column names
            for col in table['columns']:
                col_name = col['column_name'].lower()
                if col_name in question_lower:
                    score += 3
                for keyword in keywords:
                    if keyword in col_name:
                        score += 1
            
            scored_tables.append((score, table))
        
        # Sort by score and take top N tables
        scored_tables.sort(reverse=True, key=lambda x: x[0])
        relevant_tables = [t for s, t in scored_tables[:max_tables] if s > 0]
        
        # If no relevant tables found, return all tables (but limited)
        if not relevant_tables:
            relevant_tables = snapshot['tables'][:max_tables]
        
        # Build detailed context with clear column information
        context = f"Database: {snapshot['database_name']}\n"
        context += f"Relevant tables for your question:\n\n"
        
        for table in relevant_tables:
            context += f"Table: {table['table_name']}\n"
            context += "Columns:\n"
            for col in table['columns']:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                context += f"  - {col['column_name']} ({col['data_type']}) {nullable}{default}\n"
            context += "\n"
        
        return context


# For backward compatibility, keep a global instance
# But new code should create instances per session
db_service = PooledDatabaseService()
