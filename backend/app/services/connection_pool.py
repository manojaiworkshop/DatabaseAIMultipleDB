"""
Connection Pool Manager with Multi-Tenancy Support
Handles database connections efficiently with connection pooling
"""
import psycopg2
from psycopg2 import pool
from typing import Dict, Optional, Tuple
import logging
import hashlib
import time
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class ConnectionPool:
    """Manages a single connection pool for a specific database"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str,
                 min_connections: int = 1, max_connections: int = 10):
        """
        Initialize connection pool for a specific database
        
        Args:
            min_connections: Minimum number of connections to maintain
            max_connections: Maximum number of connections allowed
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        
        self.last_used = datetime.now()
        self.connection_count = 0
        self.pool = None
        
        try:
            # Create connection pool using psycopg2's SimpleConnectionPool
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=min_connections,
                maxconn=max_connections,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                # Connection timeout settings
                connect_timeout=10,
                options='-c statement_timeout=30000'  # 30 second query timeout
            )
            logger.info(f"Created connection pool for {database} (min={min_connections}, max={max_connections})")
            
        except Exception as e:
            logger.error(f"Failed to create connection pool for {database}: {e}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool"""
        if self.pool is None:
            raise ValueError("Connection pool not initialized")
        
        try:
            conn = self.pool.getconn()
            self.last_used = datetime.now()
            self.connection_count += 1
            logger.debug(f"Connection acquired from pool ({self.database}). Total: {self.connection_count}")
            return conn
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        if self.pool is None:
            return
        
        try:
            self.pool.putconn(conn)
            self.connection_count -= 1
            logger.debug(f"Connection returned to pool ({self.database}). Remaining: {self.connection_count}")
        except Exception as e:
            logger.error(f"Failed to return connection to pool: {e}")
    
    def close_all(self):
        """Close all connections in the pool"""
        if self.pool:
            try:
                self.pool.closeall()
                logger.info(f"Closed all connections for {self.database}")
            except Exception as e:
                logger.error(f"Error closing pool: {e}")
    
    def is_idle(self, timeout_minutes: int = 30) -> bool:
        """Check if pool has been idle for too long"""
        idle_time = datetime.now() - self.last_used
        return idle_time > timedelta(minutes=timeout_minutes)


class ConnectionPoolManager:
    """
    Manages multiple connection pools for different databases
    Supports multi-tenancy with session-based connection management
    """
    
    def __init__(self, min_connections: int = 1, max_connections: int = 10,
                 idle_timeout_minutes: int = 30):
        """
        Initialize the connection pool manager
        
        Args:
            min_connections: Minimum connections per pool
            max_connections: Maximum connections per pool
            idle_timeout_minutes: Close idle pools after this many minutes
        """
        self.pools: Dict[str, ConnectionPool] = {}
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.idle_timeout_minutes = idle_timeout_minutes
        
        # Thread lock for pool operations
        self.lock = threading.RLock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_idle_pools, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("ConnectionPoolManager initialized")
    
    def _generate_pool_key(self, host: str, port: int, database: str, user: str) -> str:
        """Generate unique key for a database connection"""
        connection_string = f"{host}:{port}:{database}:{user}"
        return hashlib.md5(connection_string.encode()).hexdigest()
    
    def get_or_create_pool(self, host: str, port: int, database: str, 
                           user: str, password: str) -> ConnectionPool:
        """
        Get existing pool or create new one for the database
        Thread-safe operation
        """
        pool_key = self._generate_pool_key(host, port, database, user)
        
        with self.lock:
            # Check if pool exists
            if pool_key in self.pools:
                pool = self.pools[pool_key]
                logger.debug(f"Using existing pool for {database}")
                return pool
            
            # Create new pool
            try:
                pool = ConnectionPool(
                    host=host,
                    port=port,
                    database=database,
                    user=user,
                    password=password,
                    min_connections=self.min_connections,
                    max_connections=self.max_connections
                )
                self.pools[pool_key] = pool
                logger.info(f"Created new pool for {database}. Total pools: {len(self.pools)}")
                return pool
                
            except Exception as e:
                logger.error(f"Failed to create pool for {database}: {e}")
                raise
    
    def get_connection(self, host: str, port: int, database: str, 
                      user: str, password: str):
        """
        Get a database connection from the appropriate pool
        """
        pool = self.get_or_create_pool(host, port, database, user, password)
        return pool.get_connection()
    
    def return_connection(self, host: str, port: int, database: str, 
                         user: str, conn):
        """
        Return a connection to its pool
        """
        pool_key = self._generate_pool_key(host, port, database, user)
        
        with self.lock:
            if pool_key in self.pools:
                self.pools[pool_key].return_connection(conn)
            else:
                # Pool doesn't exist anymore, close connection
                try:
                    conn.close()
                except:
                    pass
    
    def close_pool(self, host: str, port: int, database: str, user: str):
        """Close a specific connection pool"""
        pool_key = self._generate_pool_key(host, port, database, user)
        
        with self.lock:
            if pool_key in self.pools:
                pool = self.pools.pop(pool_key)
                pool.close_all()
                logger.info(f"Closed pool for {database}")
    
    def close_all_pools(self):
        """Close all connection pools"""
        with self.lock:
            for pool_key, pool in list(self.pools.items()):
                try:
                    pool.close_all()
                except Exception as e:
                    logger.error(f"Error closing pool {pool_key}: {e}")
            
            self.pools.clear()
            logger.info("All connection pools closed")
    
    def _cleanup_idle_pools(self):
        """Background thread to cleanup idle pools"""
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes
                
                with self.lock:
                    idle_pools = []
                    
                    for pool_key, pool in self.pools.items():
                        if pool.is_idle(self.idle_timeout_minutes):
                            idle_pools.append(pool_key)
                    
                    # Close idle pools
                    for pool_key in idle_pools:
                        pool = self.pools.pop(pool_key)
                        pool.close_all()
                        logger.info(f"Cleaned up idle pool: {pool.database}")
                    
                    if idle_pools:
                        logger.info(f"Cleaned up {len(idle_pools)} idle pools. Active pools: {len(self.pools)}")
                        
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")
    
    def get_stats(self) -> Dict:
        """Get statistics about connection pools"""
        with self.lock:
            return {
                "total_pools": len(self.pools),
                "pools": [
                    {
                        "database": pool.database,
                        "host": pool.host,
                        "active_connections": pool.connection_count,
                        "last_used": pool.last_used.isoformat()
                    }
                    for pool in self.pools.values()
                ]
            }


# Global connection pool manager instance
pool_manager = ConnectionPoolManager(
    min_connections=1,
    max_connections=20,
    idle_timeout_minutes=30
)
