"""
Base Database Adapter
Abstract base class defining common interface for all database adapters
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class BaseDatabaseAdapter(ABC):
    """Abstract base class for database adapters"""
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize adapter with connection parameters
        
        Args:
            connection_params: Dictionary containing connection details
        """
        self.connection_params = connection_params
        self.connection = None
        self.schema_cache = None
        self.cache_timestamp = None
    
    @property
    @abstractmethod
    def database_type(self) -> str:
        """Return the database type identifier"""
        pass
    
    @abstractmethod
    def get_connection(self):
        """Establish and return database connection"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Test database connection
        
        Returns:
            Tuple of (success, message, connection_info)
        """
        pass
    
    @abstractmethod
    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """
        Get list of all schemas/databases
        
        Returns:
            List of schema information dictionaries
        """
        pass
    
    @abstractmethod
    def get_schema_snapshot(self, schema_name: str) -> Dict[str, Any]:
        """
        Get snapshot for a specific schema
        
        Args:
            schema_name: Name of the schema
            
        Returns:
            Dictionary with schema information
        """
        pass
    
    @abstractmethod
    def get_database_snapshot(self) -> Dict[str, Any]:
        """
        Get complete database schema snapshot
        
        Returns:
            Dictionary with complete database information
        """
        pass
    
    @abstractmethod
    def execute_query(self, sql_query: str) -> Tuple[List[Dict[str, Any]], List[str], float]:
        """
        Execute SQL query and return results
        
        Args:
            sql_query: SQL query to execute
            
        Returns:
            Tuple of (results, columns, execution_time)
        """
        pass
    
    @abstractmethod
    def get_table_info(self, schema_name: str, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific table
        
        Args:
            schema_name: Schema name
            table_name: Table name
            
        Returns:
            Dictionary with table details
        """
        pass
    
    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def clear_cache(self):
        """Clear schema cache"""
        self.schema_cache = None
        self.cache_timestamp = None
    
    def serialize_value(self, value):
        """Convert non-JSON serializable types to JSON serializable types"""
        from datetime import datetime, date
        from decimal import Decimal
        
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        elif value is None:
            return None
        return value
    
    def get_sql_dialect(self) -> str:
        """
        Get SQL dialect name for LLM prompts
        
        Returns:
            SQL dialect name
        """
        return self.database_type.upper()
