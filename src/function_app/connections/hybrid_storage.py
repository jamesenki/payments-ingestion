"""
Hybrid storage connection management system.

Implements WO-30: Implement Hybrid Storage Connection Management System

This module provides a unified connection management system for both PostgreSQL
database operations and Azure Blob Storage access, ensuring efficient resource
usage and optimal performance in the serverless Azure Functions environment.
"""

import logging
import time
import threading
from typing import Optional, Dict, Any

try:
    from azure.storage.blob import BlobServiceClient
    AZURE_STORAGE_AVAILABLE = True
except ImportError:
    AZURE_STORAGE_AVAILABLE = False
    # Create a dummy class for type hints when Azure SDK is not available
    class BlobServiceClient:
        pass

from .database_pool import DatabaseConnectionPool
from ..storage.parquet_serializer import ParquetSerializer

logger = logging.getLogger(__name__)


class HybridStorageConnectionManager:
    """
    Unified connection manager for PostgreSQL and Azure Blob Storage.
    
    This class provides a single interface for managing connections to both
    PostgreSQL (via connection pool) and Azure Blob Storage, with automatic
    retry logic and error handling for both storage types.
    
    Features:
    - PostgreSQL connection pool (2-10 connections)
    - Blob Storage connection management with SDK pooling
    - Parquet serialization integration
    - Connection health validation
    - Automatic connection recycling
    - Environment-specific configuration support
    - Connection acquisition within 1 second
    """
    
    def __init__(
        self,
        postgres_connection_string: str,
        blob_storage_connection_string: str,
        postgres_min_connections: int = 2,
        postgres_max_connections: int = 10,
        postgres_connection_timeout: int = 30,
        postgres_idle_timeout: int = 300,
        parquet_compression: str = "snappy"
    ):
        """
        Initialize HybridStorageConnectionManager.
        
        Args:
            postgres_connection_string: PostgreSQL connection string
            blob_storage_connection_string: Azure Blob Storage connection string
            postgres_min_connections: Minimum PostgreSQL pool size (default: 2)
            postgres_max_connections: Maximum PostgreSQL pool size (default: 10)
            postgres_connection_timeout: PostgreSQL connection timeout in seconds (default: 30)
            postgres_idle_timeout: PostgreSQL idle timeout in seconds (default: 300)
            parquet_compression: Parquet compression algorithm (default: "snappy")
        """
        if not AZURE_STORAGE_AVAILABLE:
            raise ImportError(
                "azure-storage-blob package is required. "
                "Install with: pip install azure-storage-blob"
            )
        
        # Initialize PostgreSQL connection pool
        self.db_pool = DatabaseConnectionPool(
            connection_string=postgres_connection_string,
            min_connections=postgres_min_connections,
            max_connections=postgres_max_connections,
            connection_timeout=postgres_connection_timeout,
            idle_timeout=postgres_idle_timeout
        )
        
        # Initialize Blob Storage client
        self.blob_storage_connection_string = blob_storage_connection_string
        self._blob_service_client: Optional[BlobServiceClient] = None
        self._blob_client_lock = threading.Lock()
        
        # Initialize Parquet serializer
        self.parquet_serializer = ParquetSerializer(compression=parquet_compression)
        
        # Connection state
        self._initialized = False
        self._lock = threading.Lock()
        
        # Metrics
        self._metrics = {
            "postgres_connections_acquired": 0,
            "postgres_connections_released": 0,
            "blob_operations": 0,
            "parquet_serializations": 0,
            "parquet_deserializations": 0,
            "connection_failures": 0,
        }
        
        logger.info(
            f"HybridStorageConnectionManager initialized: "
            f"postgres_pool={postgres_min_connections}-{postgres_max_connections}, "
            f"parquet_compression={parquet_compression}"
        )
    
    def initialize(self) -> None:
        """
        Initialize all connections (PostgreSQL pool and Blob Storage client).
        
        This method should be called during function app initialization.
        Connection acquisition should complete within 1 second under normal load.
        """
        if self._initialized:
            logger.debug("HybridStorageConnectionManager already initialized")
            return
        
        with self._lock:
            if self._initialized:
                return
            
            start_time = time.time()
            
            try:
                # Initialize PostgreSQL connection pool
                self.db_pool.initialize()
                
                # Initialize Blob Storage client
                self._blob_service_client = BlobServiceClient.from_connection_string(
                    self.blob_storage_connection_string
                )
                
                # Test Blob Storage connection
                # This is a lightweight operation that validates connectivity
                try:
                    # List containers to test connection (this is a read-only operation)
                    list(self._blob_service_client.list_containers(max_results=1))
                except Exception as e:
                    logger.warning(f"Blob Storage connection test failed: {str(e)}")
                    # Continue anyway - connection might work for actual operations
                
                self._initialized = True
                elapsed = time.time() - start_time
                
                if elapsed > 1.0:
                    logger.warning(
                        f"Initialization took {elapsed:.2f}s (target: <1s)"
                    )
                
                logger.info(
                    f"HybridStorageConnectionManager initialized successfully "
                    f"(took {elapsed:.2f}s)"
                )
                
            except Exception as e:
                logger.error(f"Failed to initialize HybridStorageConnectionManager: {str(e)}", exc_info=True)
                raise
    
    def get_postgres_connection(self):
        """
        Get a PostgreSQL connection from the pool.
        
        Returns:
            psycopg2 connection object
            
        Raises:
            RuntimeError: If not initialized
            pool.PoolError: If pool is exhausted
        """
        if not self._initialized:
            raise RuntimeError("Not initialized. Call initialize() first.")
        
        try:
            conn = self.db_pool.get_connection()
            with self._lock:
                self._metrics["postgres_connections_acquired"] += 1
            return conn
        except Exception as e:
            with self._lock:
                self._metrics["connection_failures"] += 1
            logger.error(f"Failed to acquire PostgreSQL connection: {str(e)}")
            raise
    
    def return_postgres_connection(self, conn, close: bool = False) -> None:
        """
        Return a PostgreSQL connection to the pool.
        
        Args:
            conn: Connection to return
            close: If True, close the connection instead of returning to pool
        """
        try:
            self.db_pool.return_connection(conn, close=close)
            with self._lock:
                self._metrics["postgres_connections_released"] += 1
        except Exception as e:
            logger.error(f"Error returning PostgreSQL connection: {str(e)}", exc_info=True)
    
    def get_blob_service_client(self) -> BlobServiceClient:
        """
        Get the Azure Blob Storage service client.
        
        The Blob Storage SDK handles connection pooling automatically,
        so we return a singleton client instance.
        
        Returns:
            BlobServiceClient instance
            
        Raises:
            RuntimeError: If not initialized
        """
        if not self._initialized:
            raise RuntimeError("Not initialized. Call initialize() first.")
        
        if self._blob_service_client is None:
            with self._blob_client_lock:
                if self._blob_service_client is None:
                    self._blob_service_client = BlobServiceClient.from_connection_string(
                        self.blob_storage_connection_string
                    )
        
        return self._blob_service_client
    
    def get_parquet_serializer(self) -> ParquetSerializer:
        """
        Get the Parquet serializer instance.
        
        Returns:
            ParquetSerializer instance
        """
        return self.parquet_serializer
    
    def execute_with_postgres(
        self,
        operation: callable,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Any:
        """
        Execute an operation with automatic PostgreSQL connection management.
        
        This method handles connection acquisition, operation execution, and
        connection return with automatic retry logic.
        
        Args:
            operation: Callable that takes a connection as argument
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
        
        Returns:
            Result of the operation
        
        Raises:
            Exception: If operation fails after all retries
        """
        for attempt in range(max_retries):
            conn = None
            try:
                conn = self.get_postgres_connection()
                result = operation(conn)
                return result
                
            except Exception as e:
                if conn:
                    # Mark connection as potentially bad
                    self.return_postgres_connection(conn, close=True)
                    conn = None
                
                if attempt < max_retries - 1:
                    logger.warning(
                        f"PostgreSQL operation failed (attempt {attempt + 1}/{max_retries}): {str(e)}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"PostgreSQL operation failed after {max_retries} attempts: {str(e)}")
                    raise
            finally:
                if conn:
                    self.return_postgres_connection(conn)
    
    def execute_with_blob_storage(
        self,
        operation: callable,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Any:
        """
        Execute an operation with automatic Blob Storage connection management.
        
        This method handles Blob Storage client acquisition and operation
        execution with automatic retry logic.
        
        Args:
            operation: Callable that takes BlobServiceClient as argument
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
        
        Returns:
            Result of the operation
        
        Raises:
            Exception: If operation fails after all retries
        """
        for attempt in range(max_retries):
            try:
                client = self.get_blob_service_client()
                result = operation(client)
                
                with self._lock:
                    self._metrics["blob_operations"] += 1
                
                return result
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Blob Storage operation failed (attempt {attempt + 1}/{max_retries}): {str(e)}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Blob Storage operation failed after {max_retries} attempts: {str(e)}")
                    with self._lock:
                        self._metrics["connection_failures"] += 1
                    raise
    
    def serialize_to_parquet(self, events: list) -> bytes:
        """
        Serialize events to Parquet format.
        
        Args:
            events: List of events to serialize
        
        Returns:
            Parquet bytes
        """
        try:
            result = self.parquet_serializer.serialize_events(events)
            with self._lock:
                self._metrics["parquet_serializations"] += 1
            return result
        except Exception as e:
            logger.error(f"Parquet serialization failed: {str(e)}", exc_info=True)
            raise
    
    def deserialize_from_parquet(self, parquet_bytes: bytes) -> list:
        """
        Deserialize Parquet bytes to events.
        
        Args:
            parquet_bytes: Parquet bytes to deserialize
        
        Returns:
            List of events
        """
        try:
            result = self.parquet_serializer.deserialize_events(parquet_bytes)
            with self._lock:
                self._metrics["parquet_deserializations"] += 1
            return result
        except Exception as e:
            logger.error(f"Parquet deserialization failed: {str(e)}", exc_info=True)
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get connection and operation metrics.
        
        Returns:
            Dictionary with metrics including:
            - PostgreSQL pool metrics
            - Blob Storage operation counts
            - Parquet serialization counts
            - Connection failure counts
        """
        with self._lock:
            postgres_metrics = self.db_pool.get_metrics()
            
            return {
                "postgres": postgres_metrics,
                "blob_storage": {
                    "operations": self._metrics["blob_operations"],
                },
                "parquet": {
                    "serializations": self._metrics["parquet_serializations"],
                    "deserializations": self._metrics["parquet_deserializations"],
                },
                "connection_failures": self._metrics["connection_failures"],
            }
    
    def close_all(self) -> None:
        """
        Close all connections and clean up resources.
        
        This should be called during function app shutdown.
        """
        try:
            # Close PostgreSQL pool
            self.db_pool.close_all()
            
            # Blob Storage client doesn't need explicit close
            # but we can clear the reference
            self._blob_service_client = None
            
            self._initialized = False
            logger.info("HybridStorageConnectionManager closed")
            
        except Exception as e:
            logger.error(f"Error closing HybridStorageConnectionManager: {str(e)}", exc_info=True)

