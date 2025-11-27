"""
Database Adapter Factory
Factory pattern for creating database adapters based on database type
"""
from typing import Dict, Any
import logging

from .base_adapter import BaseDatabaseAdapter
from .postgres_adapter import PostgresAdapter
from .mysql_adapter import MySQLAdapter
from .oracle_adapter import OracleAdapter
from .sqlite_adapter import SQLiteAdapter

logger = logging.getLogger(__name__)


class DatabaseAdapterFactory:
    """Factory for creating database adapters"""
    
    # Registry of available adapters
    _adapters = {
        'postgresql': PostgresAdapter,
        'postgres': PostgresAdapter,
        'pg': PostgresAdapter,
        'mysql': MySQLAdapter,
        'mariadb': MySQLAdapter,
        'oracle': OracleAdapter,
        'sqlite': SQLiteAdapter,
        'sqlite3': SQLiteAdapter,
    }
    
    @classmethod
    def create_adapter(cls, database_type: str, connection_params: Dict[str, Any]) -> BaseDatabaseAdapter:
        """
        Create appropriate database adapter based on type
        
        Args:
            database_type: Type of database (postgresql, mysql, oracle, sqlite)
            connection_params: Connection parameters dictionary
            
        Returns:
            Instance of appropriate database adapter
            
        Raises:
            ValueError: If database type is not supported
        """
        database_type = database_type.lower().strip()
        
        adapter_class = cls._adapters.get(database_type)
        
        if not adapter_class:
            supported = ', '.join(set(cls._adapters.keys()))
            raise ValueError(
                f"Unsupported database type: {database_type}. "
                f"Supported types: {supported}"
            )
        
        logger.info(f"Creating {adapter_class.__name__} for {database_type}")
        return adapter_class(connection_params)
    
    @classmethod
    def get_supported_databases(cls) -> list:
        """Get list of supported database types"""
        # Return unique database types
        unique_types = set()
        type_info = []
        
        for db_type, adapter_class in cls._adapters.items():
            adapter_type = adapter_class({}).database_type
            if adapter_type not in unique_types:
                unique_types.add(adapter_type)
                type_info.append({
                    'type': adapter_type,
                    'aliases': [k for k, v in cls._adapters.items() if v == adapter_class],
                    'adapter_class': adapter_class.__name__
                })
        
        return type_info
    
    @classmethod
    def register_adapter(cls, database_type: str, adapter_class: type):
        """
        Register a new database adapter
        
        Args:
            database_type: Type identifier for the database
            adapter_class: Adapter class (must inherit from BaseDatabaseAdapter)
        """
        if not issubclass(adapter_class, BaseDatabaseAdapter):
            raise TypeError(f"{adapter_class} must inherit from BaseDatabaseAdapter")
        
        cls._adapters[database_type.lower()] = adapter_class
        logger.info(f"Registered adapter {adapter_class.__name__} for type: {database_type}")
