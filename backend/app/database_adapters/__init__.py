"""
Database Adapters Package
Provides unified interface for different database systems
"""
from .base_adapter import BaseDatabaseAdapter
from .postgres_adapter import PostgresAdapter
from .mysql_adapter import MySQLAdapter
from .oracle_adapter import OracleAdapter
from .sqlite_adapter import SQLiteAdapter
from .adapter_factory import DatabaseAdapterFactory

__all__ = [
    'BaseDatabaseAdapter',
    'PostgresAdapter',
    'MySQLAdapter',
    'OracleAdapter',
    'SQLiteAdapter',
    'DatabaseAdapterFactory'
]
