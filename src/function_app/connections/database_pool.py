"""
Database connection pool management.

Implements WO-41: Implement Database Connection Pool Management

This module provides efficient database connection management for the serverless
Azure Functions environment using psycopg2 connection pooling to balance resource
usage and throughput while maintaining connection health.
"""

import logging
import time
import threading
from typing import Optional
from datetime import datetime, timedelta

import psycopg2
from psycopg2 import pool, OperationalError
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """
    Database connection pool manager with health validation and recycling.
    
    This class manages a pool of PostgreSQL connections with:
    - Configurable min/max pool size
    - Connection health validation
    - Automatic connection recycling
    - Graceful pool exhaustion handling
    - Connection metrics logging
    
    Features:
    - SimpleConnectionPool with 2-10 connections per function instance
    - Connection timeout of 30 seconds
    - Idle timeout of 300 seconds (5 minutes) with automatic recycling
    - Health validation using 'SELECT 1' query
    - Metrics tracking for monitoring
    """
    
    def __init__(
        self,
        connection_string: str,
        min_connections: int = 2,
        max_connections: int = 10,
        connection_timeout: int = 30,
        idle_timeout: int = 300
    ):
        """
        Initialize DatabaseConnectionPool.
        
        Args:
            connection_string: PostgreSQL connection string
            min_connections: Minimum number of connections in pool (default: 2)
            max_connections: Maximum number of connections in pool (default: 10)
            connection_timeout: Connection timeout in seconds (default: 30)
            idle_timeout: Idle connection timeout in seconds (default: 300 = 5 minutes)
        """
        self.connection_string = connection_string
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout
        
        self._pool: Optional[pool.SimpleConnectionPool] = None
        self._connection_times: dict = {}  # Track when connections were acquired
        self._lock = threading.Lock()
        self._initialized = False
        
        # Metrics
        self._metrics = {
            "total_acquired": 0,
            "total_released": 0,
            "pool_exhaustions": 0,
            "health_check_failures": 0,
            "recycled_connections": 0,
            "total_acquisition_time_ms": 0.0,
        }
        
        logger.info(
            f"DatabaseConnectionPool initialized: "
            f"min={min_connections}, max={max_connections}, "
            f"timeout={connection_timeout}s, idle_timeout={idle_timeout}s"
        )
    
    def initialize(self) -> None:
        """
        Initialize the connection pool.
        
        This method creates the SimpleConnectionPool and should be called
        during function app initialization. It is safe to call multiple times.
        """
        if self._initialized and self._pool is not None:
            logger.debug("Connection pool already initialized")
            return
        
        with self._lock:
            if self._initialized and self._pool is not None:
                return
            
            try:
                self._pool = psycopg2.pool.SimpleConnectionPool(
                    self.min_connections,
                    self.max_connections,
                    self.connection_string,
                    connect_timeout=self.connection_timeout
                )
                
                if self._pool is None:
                    raise RuntimeError("Failed to create connection pool")
                
                self._initialized = True
                logger.info(
                    f"Connection pool initialized: "
                    f"{self.min_connections}-{self.max_connections} connections"
                )
                
            except Exception as e:
                logger.error(f"Failed to initialize connection pool: {str(e)}", exc_info=True)
                raise
    
    def get_connection(self):
        """
        Get a connection from the pool.
        
        This method acquires a connection from the pool, validates its health,
        and returns it. If the pool is exhausted, it handles the error gracefully.
        Connection acquisition should complete within 1 second under normal load.
        
        Returns:
            psycopg2 connection object
            
        Raises:
            RuntimeError: If pool is not initialized
            pool.PoolError: If pool is exhausted or connection fails
        """
        if not self._initialized or self._pool is None:
            raise RuntimeError("Connection pool not initialized. Call initialize() first.")
        
        start_time = time.time()
        
        try:
            # Get connection from pool
            conn = self._pool.getconn()
            
            if conn is None:
                # Pool exhausted
                with self._lock:
                    self._metrics["pool_exhaustions"] += 1
                
                logger.warning("Connection pool exhausted")
                raise pool.PoolError("Connection pool exhausted")
            
            # Track acquisition time
            acquisition_time = (time.time() - start_time) * 1000
            
            with self._lock:
                self._metrics["total_acquired"] += 1
                self._metrics["total_acquisition_time_ms"] += acquisition_time
                self._connection_times[id(conn)] = datetime.utcnow()
            
            # Validate connection health
            if not self._validate_connection(conn):
                # Connection is unhealthy, try to get another one
                self._pool.putconn(conn, close=True)
                with self._lock:
                    self._metrics["health_check_failures"] += 1
                
                # Try once more
                conn = self._pool.getconn()
                if conn is None:
                    raise pool.PoolError("Connection pool exhausted after health check failure")
                
                if not self._validate_connection(conn):
                    self._pool.putconn(conn, close=True)
                    raise pool.PoolError("All connections in pool are unhealthy")
            
            # Check if connection needs recycling (idle timeout)
            if self._should_recycle_connection(conn):
                logger.debug("Recycling idle connection")
                self._pool.putconn(conn, close=True)
                with self._lock:
                    self._metrics["recycled_connections"] += 1
                
                # Get a fresh connection
                conn = self._pool.getconn()
                if conn is None:
                    raise pool.PoolError("Connection pool exhausted during recycling")
                
                if not self._validate_connection(conn):
                    self._pool.putconn(conn, close=True)
                    raise pool.PoolError("Recycled connection is unhealthy")
            
            elapsed = (time.time() - start_time) * 1000
            if elapsed > 1000:  # 1 second
                logger.warning(f"Connection acquisition took {elapsed:.2f}ms (target: <1000ms)")
            
            return conn
            
        except pool.PoolError:
            raise
        except Exception as e:
            logger.error(f"Error acquiring connection: {str(e)}", exc_info=True)
            raise pool.PoolError(f"Failed to acquire connection: {str(e)}") from e
    
    def return_connection(self, conn, close: bool = False) -> None:
        """
        Return a connection to the pool.
        
        Args:
            conn: Connection to return
            close: If True, close the connection instead of returning to pool
        """
        if not self._initialized or self._pool is None:
            logger.warning("Attempted to return connection to uninitialized pool")
            return
        
        try:
            # Remove from tracking
            conn_id = id(conn)
            with self._lock:
                if conn_id in self._connection_times:
                    del self._connection_times[conn_id]
                self._metrics["total_released"] += 1
            
            # Return to pool or close
            self._pool.putconn(conn, close=close)
            
        except Exception as e:
            logger.error(f"Error returning connection: {str(e)}", exc_info=True)
            # Try to close the connection if returning failed
            try:
                conn.close()
            except Exception:
                pass
    
    def _validate_connection(self, conn) -> bool:
        """
        Validate connection health using 'SELECT 1' query.
        
        Args:
            conn: Connection to validate
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except (OperationalError, Exception) as e:
            logger.warning(f"Connection health check failed: {str(e)}")
            return False
    
    def _should_recycle_connection(self, conn) -> bool:
        """
        Check if connection should be recycled based on idle timeout.
        
        Args:
            conn: Connection to check
        
        Returns:
            True if connection should be recycled, False otherwise
        """
        conn_id = id(conn)
        with self._lock:
            if conn_id not in self._connection_times:
                return False
            
            last_used = self._connection_times[conn_id]
            idle_duration = datetime.utcnow() - last_used
            
            return idle_duration.total_seconds() > self.idle_timeout
    
    def get_metrics(self) -> dict:
        """
        Get connection pool metrics.
        
        Returns:
            Dictionary with pool metrics including:
            - total_acquired: Total connections acquired
            - total_released: Total connections released
            - pool_exhaustions: Number of times pool was exhausted
            - health_check_failures: Number of health check failures
            - recycled_connections: Number of connections recycled
            - avg_acquisition_time_ms: Average connection acquisition time
            - active_connections: Current number of active connections
            - pool_size: Current pool size
        """
        with self._lock:
            active = len(self._connection_times)
            
            # Get pool size (min and max)
            pool_size = {
                "min": self.min_connections,
                "max": self.max_connections,
            }
            
            total_acquired = self._metrics["total_acquired"]
            avg_time = (
                self._metrics["total_acquisition_time_ms"] / total_acquired
                if total_acquired > 0
                else 0.0
            )
            
            return {
                "total_acquired": self._metrics["total_acquired"],
                "total_released": self._metrics["total_released"],
                "pool_exhaustions": self._metrics["pool_exhaustions"],
                "health_check_failures": self._metrics["health_check_failures"],
                "recycled_connections": self._metrics["recycled_connections"],
                "avg_acquisition_time_ms": avg_time,
                "active_connections": active,
                "pool_size": pool_size,
            }
    
    def close_all(self) -> None:
        """
        Close all connections in the pool.
        
        This should be called during function app shutdown to properly
        clean up resources.
        """
        if self._pool is not None:
            try:
                self._pool.closeall()
                logger.info("All connections in pool closed")
            except Exception as e:
                logger.error(f"Error closing connection pool: {str(e)}", exc_info=True)
            finally:
                self._pool = None
                self._initialized = False
                with self._lock:
                    self._connection_times.clear()

