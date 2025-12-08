"""
Unit tests for HybridStorageConnectionManager.

Tests WO-30: Implement Hybrid Storage Connection Management System
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Import hybrid_storage directly to handle Azure SDK dependencies
import sys
from pathlib import Path

# Mock Azure SDK before importing
from unittest.mock import MagicMock
azure_mock = MagicMock()
sys.modules['azure'] = azure_mock
sys.modules['azure.storage'] = MagicMock()
sys.modules['azure.storage.blob'] = MagicMock()
BlobServiceClient = MagicMock()
sys.modules['azure.storage.blob'].BlobServiceClient = BlobServiceClient
sys.modules['azure.core'] = MagicMock()
sys.modules['azure.core.exceptions'] = MagicMock()

# Import database_pool first
db_pool_path = Path(__file__).parent.parent.parent.parent / "src" / "function_app" / "connections" / "database_pool.py"
import importlib.util
spec = importlib.util.spec_from_file_location("database_pool", db_pool_path)
db_pool_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db_pool_module)
DatabaseConnectionPool = db_pool_module.DatabaseConnectionPool

# Now import hybrid_storage
hybrid_path = Path(__file__).parent.parent.parent.parent / "src" / "function_app" / "connections" / "hybrid_storage.py"
spec = importlib.util.spec_from_file_location("hybrid_storage", hybrid_path)
hybrid_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hybrid_module)
HybridStorageConnectionManager = hybrid_module.HybridStorageConnectionManager


class TestHybridStorageConnectionManager:
    """Tests for HybridStorageConnectionManager class."""
    
    @patch('azure.storage.blob.BlobServiceClient')
    @patch.object(DatabaseConnectionPool, '__init__', return_value=None)
    @patch.object(DatabaseConnectionPool, 'initialize')
    def test_manager_initialization(self, mock_init, mock_db_init, mock_blob_client):
        """Test HybridStorageConnectionManager initialization."""
        pg_conn_str = "postgresql://user:pass@localhost/db"
        blob_conn_str = "DefaultEndpointsProtocol=https;AccountName=test;..."
        
        mock_service = MagicMock()
        mock_blob_client.from_connection_string.return_value = mock_service
        
        # Check if HybridStorageConnectionManager requires Azure SDK
        try:
            manager = HybridStorageConnectionManager(
                postgres_connection_string=pg_conn_str,
                blob_storage_connection_string=blob_conn_str
            )
            assert manager is not None
        except ImportError:
            pytest.skip("Azure SDK not available for testing")
    
    @patch('azure.storage.blob.BlobServiceClient')
    @patch.object(DatabaseConnectionPool, '__init__', return_value=None)
    @patch.object(DatabaseConnectionPool, 'initialize')
    def test_get_pg_connection(self, mock_init, mock_db_init, mock_blob_client):
        """Test getting PostgreSQL connection."""
        pg_conn_str = "postgresql://user:pass@localhost/db"
        blob_conn_str = "DefaultEndpointsProtocol=https;AccountName=test;..."
        
        mock_blob_client.from_connection_string.return_value = MagicMock()
        mock_db_pool = MagicMock()
        mock_conn = MagicMock()
        mock_db_pool.get_connection.return_value = mock_conn
        
        manager = HybridStorageConnectionManager(
            postgres_connection_string=pg_conn_str,
            blob_storage_connection_string=blob_conn_str
        )
        manager.db_pool = mock_db_pool
        
        conn = manager.get_pg_connection()
        
        assert conn == mock_conn
        mock_db_pool.get_connection.assert_called_once()
    
    @patch('azure.storage.blob.BlobServiceClient')
    @patch.object(DatabaseConnectionPool, '__init__', return_value=None)
    @patch.object(DatabaseConnectionPool, 'initialize')
    def test_put_pg_connection(self, mock_init, mock_db_init, mock_blob_client):
        """Test returning PostgreSQL connection."""
        pg_conn_str = "postgresql://user:pass@localhost/db"
        blob_conn_str = "DefaultEndpointsProtocol=https;AccountName=test;..."
        
        mock_blob_client.from_connection_string.return_value = MagicMock()
        mock_db_pool = MagicMock()
        
        manager = HybridStorageConnectionManager(
            postgres_connection_string=pg_conn_str,
            blob_storage_connection_string=blob_conn_str
        )
        manager.db_pool = mock_db_pool
        
        mock_conn = MagicMock()
        manager.put_pg_connection(mock_conn)
        
        mock_db_pool.put_connection.assert_called_once_with(mock_conn)
    
    @patch('azure.storage.blob.BlobServiceClient')
    @patch.object(DatabaseConnectionPool, '__init__', return_value=None)
    @patch.object(DatabaseConnectionPool, 'initialize')
    def test_get_blob_client(self, mock_init, mock_db_init, mock_blob_client):
        """Test getting Blob client."""
        pg_conn_str = "postgresql://user:pass@localhost/db"
        blob_conn_str = "DefaultEndpointsProtocol=https;AccountName=test;..."
        
        mock_service_client = MagicMock()
        mock_blob_client_instance = MagicMock()
        mock_service_client.get_blob_client.return_value = mock_blob_client_instance
        mock_blob_client.from_connection_string.return_value = mock_service_client
        
        manager = HybridStorageConnectionManager(
            postgres_connection_string=pg_conn_str,
            blob_storage_connection_string=blob_conn_str
        )
        
        blob_client = manager.get_blob_client("container", "blob")
        
        assert blob_client == mock_blob_client_instance
        mock_service_client.get_blob_client.assert_called_once_with(
            container="container", blob="blob"
        )
    
    @patch('azure.storage.blob.BlobServiceClient')
    @patch.object(DatabaseConnectionPool, '__init__', return_value=None)
    @patch.object(DatabaseConnectionPool, 'initialize')
    def test_get_parquet_serializer(self, mock_init, mock_db_init, mock_blob_client):
        """Test getting Parquet serializer."""
        pg_conn_str = "postgresql://user:pass@localhost/db"
        blob_conn_str = "DefaultEndpointsProtocol=https;AccountName=test;..."
        
        mock_blob_client.from_connection_string.return_value = MagicMock()
        
        manager = HybridStorageConnectionManager(
            postgres_connection_string=pg_conn_str,
            blob_storage_connection_string=blob_conn_str,
            parquet_compression="gzip"
        )
        
        serializer = manager.get_parquet_serializer()
        
        assert serializer is not None
        assert serializer.compression == "gzip"
    
    @patch('azure.storage.blob.BlobServiceClient')
    @patch.object(DatabaseConnectionPool, '__init__', return_value=None)
    @patch.object(DatabaseConnectionPool, 'initialize')
    @patch.object(DatabaseConnectionPool, 'get_metrics')
    def test_get_metrics(self, mock_get_metrics, mock_init, mock_db_init, mock_blob_client):
        """Test getting combined metrics."""
        pg_conn_str = "postgresql://user:pass@localhost/db"
        blob_conn_str = "DefaultEndpointsProtocol=https;AccountName=test;..."
        
        mock_blob_client.from_connection_string.return_value = MagicMock()
        mock_get_metrics.return_value = {"active": 2, "idle": 3}
        
        manager = HybridStorageConnectionManager(
            postgres_connection_string=pg_conn_str,
            blob_storage_connection_string=blob_conn_str
        )
        manager.db_pool = MagicMock()
        manager.db_pool.get_metrics = mock_get_metrics
        
        metrics = manager.get_metrics()
        
        assert "postgresql_pool" in metrics
        assert "blob_storage_client_initialized" in metrics
    
    @patch('azure.storage.blob.BlobServiceClient')
    @patch.object(DatabaseConnectionPool, '__init__', return_value=None)
    @patch.object(DatabaseConnectionPool, 'initialize')
    @patch.object(DatabaseConnectionPool, 'close_all')
    def test_close_all_connections(self, mock_close, mock_init, mock_db_init, mock_blob_client):
        """Test closing all connections."""
        pg_conn_str = "postgresql://user:pass@localhost/db"
        blob_conn_str = "DefaultEndpointsProtocol=https;AccountName=test;..."
        
        mock_service_client = MagicMock()
        mock_blob_client.from_connection_string.return_value = mock_service_client
        
        manager = HybridStorageConnectionManager(
            postgres_connection_string=pg_conn_str,
            blob_storage_connection_string=blob_conn_str
        )
        manager.db_pool = MagicMock()
        manager.db_pool.close_all = mock_close
        
        manager.close_all_connections()
        
        mock_close.assert_called_once()

