"""
Oracle Database Adapter
Adapter for Oracle databases
"""
import cx_Oracle
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from .base_adapter import BaseDatabaseAdapter

logger = logging.getLogger(__name__)


class OracleAdapter(BaseDatabaseAdapter):
    """Oracle database adapter"""
    
    @property
    def database_type(self) -> str:
        return "oracle"
    
    def get_connection(self):
        """Get Oracle connection"""
        if not self.connection_params:
            raise ValueError("Database connection not configured")
        
        params = self.connection_params
        
        # Oracle connection can use SID or Service Name
        if params.get('sid'):
            dsn = cx_Oracle.makedsn(
                params['host'],
                params.get('port', 1521),
                sid=params['sid']
            )
        else:
            # Default to XEPDB1 for Oracle XE, or use provided service_name
            dsn = cx_Oracle.makedsn(
                params['host'],
                params.get('port', 1521),
                service_name=params.get('service_name', 'XEPDB1')
            )
        
        return cx_Oracle.connect(
            user=params['username'],
            password=params['password'],
            dsn=dsn,
            encoding="UTF-8"
        )
    
    def test_connection(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Test Oracle connection"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get database info
            cursor.execute("SELECT * FROM v$version WHERE banner LIKE 'Oracle%'")
            version_row = cursor.fetchone()
            version = version_row[0] if version_row else "Unknown"
            
            cursor.execute("SELECT sys_context('USERENV','DB_NAME') FROM dual")
            database = cursor.fetchone()[0]
            
            cursor.execute("SELECT USER FROM dual")
            user = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            info = {
                "database": database,
                "user": user,
                "version": version,
                "database_type": self.database_type,
                "sid": self.connection_params.get('sid'),
                "service_name": self.connection_params.get('service_name')
            }
            
            return True, "Connection successful", info
            
        except cx_Oracle.Error as e:
            logger.error(f"Connection test failed: {e}")
            return False, str(e), None
    
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get list of Oracle schemas - returns only the current connected user's schema"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get current user
            cursor.execute("SELECT USER FROM dual")
            current_user = cursor.fetchone()[0]
            
            # Return only the current user's schema
            # This ensures users only see their own tables and objects
            schemas = []
            
            # Count tables in current user's schema
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_tables
            """)
            table_count = cursor.fetchone()[0]
            
            # Count views in current user's schema  
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_views
            """)
            view_count = cursor.fetchone()[0]
            
            schemas.append({
                'schema_name': current_user,
                'table_count': table_count,
                'view_count': view_count,
                'owner': current_user
            })
            
            cursor.close()
            return schemas
            
        except Exception as e:
            print(f"Error getting schemas: {str(e)}")
            # Fallback: return current user
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT USER FROM dual")
                current_user = cursor.fetchone()[0]
                cursor.close()
                return [{
                    'schema_name': current_user,
                    'table_count': 0,
                    'view_count': 0,
                    'owner': current_user
                }]
            except:
                return []
    
    def _get_schema_info_OLD_METHOD(self) -> List[Dict[str, Any]]:
        """OLD METHOD - kept for reference - showed all accessible schemas"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get distinct schema owners from tables the user can access
            cursor.execute("""
                SELECT DISTINCT owner as schema_name
                FROM all_tables
                WHERE owner NOT IN (
                    'SYS', 'SYSTEM', 'DBSNMP', 'OUTLN', 'MDSYS', 'ORDSYS', 'ORDDATA',
                    'CTXSYS', 'DSSYS', 'PERFSTAT', 'WKPROXY', 'WKSYS', 'WMSYS', 'XDB',
                    'ANONYMOUS', 'ODM', 'ODM_MTR', 'OLAPSYS', 'TRACESVR', 'REPADMIN',
                    'APEX_PUBLIC_USER', 'FLOWS_FILES', 'APEX_040000', 'APEX_040200',
                    'SPATIAL_CSW_ADMIN_USR', 'SPATIAL_WFS_ADMIN_USR', 'EXFSYS',
                    'LBACSYS', 'SQLTXPLAIN', 'SQLTXADMIN', 'GSMADMIN_INTERNAL',
                    'APPQOSSYS', 'OJVMSYS', 'ORDPLUGINS', 'SI_INFORMTN_SCHEMA',
                    'AUDSYS', 'DVSYS', 'DBSFWUSER', 'REMOTE_SCHEDULER_AGENT'
                )
                ORDER BY owner
            """)
            
            # This old code is kept above for reference but not executed
            return []
            
        except Exception as e:
            logger.error(f"Failed to get schemas (old method): {e}")
            return []
    
    def get_schema_snapshot(self, schema_name: str) -> Dict[str, Any]:
        """Get Oracle schema snapshot"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get tables for this schema
            cursor.execute("""
                SELECT table_name
                FROM all_tables
                WHERE owner = :owner
                ORDER BY table_name
            """, owner=schema_name.upper())
            
            tables = [row[0] for row in cursor]
            
            snapshot = {
                'database_name': self.connection_params.get('sid') or self.connection_params.get('service_name'),
                'schema_name': schema_name,
                'database_type': self.database_type,
                'tables': [],
                'total_tables': len(tables),
                'timestamp': datetime.now().isoformat()
            }
            
            # Process each table
            for table_name in tables:
                # Get columns
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        nullable,
                        data_default
                    FROM all_tab_columns
                    WHERE owner = :owner AND table_name = :table_name
                    ORDER BY column_id
                """, owner=schema_name.upper(), table_name=table_name)
                
                columns = []
                for col_row in cursor:
                    columns.append({
                        'column_name': col_row[0],
                        'data_type': col_row[1],
                        'is_nullable': col_row[2],
                        'column_default': col_row[3]
                    })
                
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
        """Get complete Oracle database snapshot"""
        try:
            # For Oracle, get current user's schema by default
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT USER FROM dual")
            current_user = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            # Get snapshot for current user's schema
            return self.get_schema_snapshot(current_user)
            
        except Exception as e:
            logger.error(f"Failed to get database snapshot: {e}")
            raise
    
    def execute_query(self, sql_query: str) -> Tuple[List[Dict[str, Any]], List[str], float]:
        """Execute Oracle query"""
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
                # Handle DML statements
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
        """Get detailed Oracle table information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get columns
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    data_length,
                    nullable,
                    data_default
                FROM all_tab_columns
                WHERE owner = :owner AND table_name = :table_name
                ORDER BY column_id
            """, owner=schema_name.upper(), table_name=table_name.upper())
            
            columns = []
            for row in cursor:
                columns.append({
                    'column_name': row[0],
                    'data_type': row[1],
                    'data_length': row[2],
                    'is_nullable': row[3],
                    'column_default': row[4]
                })
            
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
        return "Oracle SQL"
