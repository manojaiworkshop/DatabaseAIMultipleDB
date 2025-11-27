"""
MySQL Database Adapter
Adapter for MySQL/MariaDB databases
"""
import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from .base_adapter import BaseDatabaseAdapter

logger = logging.getLogger(__name__)


class MySQLAdapter(BaseDatabaseAdapter):
    """MySQL/MariaDB database adapter"""
    
    @property
    def database_type(self) -> str:
        return "mysql"
    
    def get_connection(self):
        """Get MySQL connection"""
        if not self.connection_params:
            raise ValueError("Database connection not configured")
        
        params = self.connection_params
        
        return mysql.connector.connect(
            host=params['host'],
            port=params.get('port', 3306),
            database=params.get('database', ''),
            user=params['username'],
            password=params['password'],
            charset='utf8mb4',
            collation='utf8mb4_general_ci'
        )
    
    def test_connection(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Test MySQL connection"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get database info
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT DATABASE()")
            database = cursor.fetchone()[0]
            
            cursor.execute("SELECT USER()")
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
            
        except Error as e:
            logger.error(f"Connection test failed: {e}")
            return False, str(e), None
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get list of all MySQL databases/schemas"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get all databases except system databases
            cursor.execute("""
                SELECT 
                    SCHEMA_NAME as schema_name,
                    DEFAULT_CHARACTER_SET_NAME as charset,
                    DEFAULT_COLLATION_NAME as collation
                FROM information_schema.SCHEMATA
                WHERE SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                ORDER BY SCHEMA_NAME
            """)
            schemas = cursor.fetchall()
            
            # Get table count for each schema
            for schema in schemas:
                schema_name = schema['schema_name']
                cursor.execute("""
                    SELECT COUNT(*) as table_count
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                """, (schema_name,))
                result = cursor.fetchone()
                schema['table_count'] = result['table_count'] if result else 0
                
                # Get view count
                cursor.execute("""
                    SELECT COUNT(*) as view_count
                    FROM information_schema.VIEWS
                    WHERE TABLE_SCHEMA = %s
                """, (schema_name,))
                result = cursor.fetchone()
                schema['view_count'] = result['view_count'] if result else 0
            
            cursor.close()
            conn.close()
            
            logger.info(f"Found {len(schemas)} schemas")
            return schemas
            
        except Exception as e:
            logger.error(f"Failed to get schemas: {e}")
            raise
    
    def get_schema_snapshot(self, schema_name: str) -> Dict[str, Any]:
        """Get MySQL schema/database snapshot"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get tables
            cursor.execute("""
                SELECT TABLE_NAME as table_name
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """, (schema_name,))
            tables = cursor.fetchall()
            
            snapshot = {
                'database_name': schema_name,
                'schema_name': schema_name,  # In MySQL, database = schema
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
                        COLUMN_NAME as column_name,
                        DATA_TYPE as data_type,
                        IS_NULLABLE as is_nullable,
                        COLUMN_DEFAULT as column_default,
                        COLUMN_KEY as column_key,
                        EXTRA as extra
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (schema_name, table_name))
                columns = cursor.fetchall()
                
                snapshot['tables'].append({
                    'schema_name': schema_name,
                    'table_name': table_name,
                    'full_name': f"{schema_name}.{table_name}",
                    'columns': columns
                })
            
            cursor.close()
            conn.close()
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to get schema snapshot: {e}")
            raise
    
    def get_database_snapshot(self) -> Dict[str, Any]:
        """Get complete MySQL database snapshot"""
        try:
            # Get current database or all databases
            current_db = self.connection_params.get('database')
            
            if current_db:
                # Get snapshot for current database only
                return self.get_schema_snapshot(current_db)
            
            # Get all databases
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT TABLE_SCHEMA, TABLE_NAME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)
            tables = cursor.fetchall()
            
            snapshot = {
                'database_name': current_db or 'all_databases',
                'database_type': self.database_type,
                'connection_info': {
                    'host': self.connection_params.get('host'),
                    'port': self.connection_params.get('port', 3306),
                    'database': current_db
                },
                'tables': [],
                'total_tables': len(tables),
                'timestamp': datetime.now().isoformat()
            }
            
            # Process tables
            for table in tables:
                table_schema = table['TABLE_SCHEMA']
                table_name = table['TABLE_NAME']
                
                # Get columns
                cursor.execute("""
                    SELECT 
                        COLUMN_NAME as column_name,
                        DATA_TYPE as data_type,
                        IS_NULLABLE as is_nullable,
                        COLUMN_DEFAULT as column_default
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (table_schema, table_name))
                columns = cursor.fetchall()
                
                snapshot['tables'].append({
                    'schema_name': table_schema,
                    'table_name': table_name,
                    'full_name': f"{table_schema}.{table_name}",
                    'columns': columns
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
        """Execute MySQL query"""
        import time
        
        try:
            start_time = time.time()
            
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(sql_query)
            
            # Handle SELECT queries
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                results = [
                    {k: self.serialize_value(v) for k, v in row.items()}
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
        """Get detailed MySQL table information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get columns
            cursor.execute("""
                SELECT 
                    COLUMN_NAME as column_name,
                    DATA_TYPE as data_type,
                    IS_NULLABLE as is_nullable,
                    COLUMN_DEFAULT as column_default,
                    CHARACTER_MAXIMUM_LENGTH as character_maximum_length,
                    COLUMN_KEY as column_key,
                    EXTRA as extra
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (schema_name, table_name))
            columns = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                'schema_name': schema_name,
                'table_name': table_name,
                'columns': columns
            }
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            raise
    
    def get_sql_dialect(self) -> str:
        """Get SQL dialect name"""
        return "MySQL"
