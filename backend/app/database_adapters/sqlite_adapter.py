"""
SQLite Database Adapter
Adapter for SQLite databases (file-based)
"""
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import os

from .base_adapter import BaseDatabaseAdapter

logger = logging.getLogger(__name__)


class SQLiteAdapter(BaseDatabaseAdapter):
    """SQLite database adapter"""
    
    @property
    def database_type(self) -> str:
        return "sqlite"
    
    def get_connection(self):
        """Get SQLite connection"""
        if not self.connection_params:
            raise ValueError("Database connection not configured")
        
        # SQLite uses file path as database
        db_path = self.connection_params.get('database') or self.connection_params.get('file_path')
        
        if not db_path:
            raise ValueError("Database file path not specified")
        
        # Check if file exists (except for :memory:)
        if db_path != ':memory:' and not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def test_connection(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Test SQLite connection"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get SQLite version
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            
            # Get database file path
            db_path = self.connection_params.get('database') or self.connection_params.get('file_path')
            
            # Get database size
            if db_path != ':memory:':
                db_size = os.path.getsize(db_path)
            else:
                db_size = 0
            
            cursor.close()
            conn.close()
            
            info = {
                "database": db_path,
                "version": f"SQLite {version}",
                "size_bytes": db_size,
                "database_type": self.database_type
            }
            
            return True, "Connection successful", info
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, str(e), None
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get list of all SQLite schemas (main database)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # SQLite has only 'main' schema by default
            # Get table count
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            table_count = cursor.fetchone()[0]
            
            # Get view count
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sqlite_master 
                WHERE type='view'
            """)
            view_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            schemas = [{
                'schema_name': 'main',
                'table_count': table_count,
                'view_count': view_count
            }]
            
            logger.info(f"Found {len(schemas)} schema(s)")
            return schemas
            
        except Exception as e:
            logger.error(f"Failed to get schemas: {e}")
            raise
    
    def get_schema_snapshot(self, schema_name: str = 'main') -> Dict[str, Any]:
        """Get SQLite schema snapshot"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get tables
            cursor.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            snapshot = {
                'database_name': self.connection_params.get('database') or self.connection_params.get('file_path'),
                'schema_name': 'main',
                'database_type': self.database_type,
                'tables': [],
                'views': [],
                'total_tables': len(tables),
                'total_views': 0,
                'timestamp': datetime.now().isoformat()
            }
            
            # Process each table
            for table_name in tables:
                # Get columns using PRAGMA
                cursor.execute(f"PRAGMA table_info('{table_name}')")
                pragma_cols = cursor.fetchall()
                
                columns = []
                for col in pragma_cols:
                    columns.append({
                        'column_name': col[1],  # name
                        'data_type': col[2],     # type
                        'is_nullable': 'YES' if col[3] == 0 else 'NO',  # notnull
                        'column_default': col[4],  # dflt_value
                        'is_primary_key': col[5] == 1  # pk
                    })
                
                snapshot['tables'].append({
                    'schema_name': 'main',
                    'table_name': table_name,
                    'full_name': table_name,
                    'columns': columns
                })
            
            cursor.close()
            conn.close()
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to get schema snapshot: {e}")
            raise
    
    def get_database_snapshot(self) -> Dict[str, Any]:
        """Get complete SQLite database snapshot"""
        # For SQLite, schema snapshot = database snapshot
        return self.get_schema_snapshot('main')
    
    def execute_query(self, sql_query: str) -> Tuple[List[Dict[str, Any]], List[str], float]:
        """Execute SQLite query"""
        import time
        
        try:
            start_time = time.time()
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            
            # Handle SELECT queries
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                results = [
                    {columns[i]: self.serialize_value(row[i]) for i in range(len(columns))}
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
        """Get detailed SQLite table information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get columns using PRAGMA
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            pragma_cols = cursor.fetchall()
            
            columns = []
            for col in pragma_cols:
                columns.append({
                    'column_name': col[1],
                    'data_type': col[2],
                    'is_nullable': 'YES' if col[3] == 0 else 'NO',
                    'column_default': col[4],
                    'is_primary_key': col[5] == 1
                })
            
            cursor.close()
            conn.close()
            
            return {
                'schema_name': 'main',
                'table_name': table_name,
                'columns': columns
            }
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            raise
    
    def get_sql_dialect(self) -> str:
        """Get SQL dialect name"""
        return "SQLite"
