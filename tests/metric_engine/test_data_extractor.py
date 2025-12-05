"""
Unit tests for data extractor.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch, call
from datetime import datetime, timedelta
from decimal import Decimal

from src.metric_engine.data_extractor import DataExtractor
from src.metric_engine.models import RawTransaction


class TestDataExtractor:
    """Tests for DataExtractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create a DataExtractor instance."""
        return DataExtractor(
            connection_string="postgresql://test:test@localhost/test",
            batch_size=100,
            max_retries=3,
            retry_delay_seconds=1
        )
    
    @pytest.fixture
    def sample_db_row(self):
        """Sample database row."""
        return {
            "transaction_id": "tx-123",
            "transaction_timestamp": datetime.now(),
            "amount": Decimal("100.50"),
            "currency": "USD",
            "payment_method": "credit_card",
            "payment_status": "completed",
            "customer_id": "cust-123",
            "customer_email": "test@example.com",
            "customer_country": "US",
            "merchant_id": "merch-123",
            "merchant_name": "Test Merchant",
            "merchant_category": "retail",
            "transaction_type": None,
            "channel": None,
            "device_type": None,
            "metadata": None
        }
    
    def test_row_to_transaction(self, extractor, sample_db_row):
        """Test converting database row to RawTransaction."""
        transaction = extractor._row_to_transaction(sample_db_row)
        
        assert isinstance(transaction, RawTransaction)
        assert transaction.transaction_id == "tx-123"
        assert transaction.amount == Decimal("100.50")
        assert transaction.currency == "USD"
    
    def test_build_query_no_filters(self, extractor):
        """Test building query without filters."""
        query = extractor._build_query(None, None, None)
        
        assert "SELECT * FROM NormalizedTransactions" in query
        assert "WHERE 1=1" in query
        assert "ORDER BY transaction_timestamp ASC" in query
    
    def test_build_query_with_time_filters(self, extractor):
        """Test building query with time filters."""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        query = extractor._build_query(start_time, end_time, None)
        
        assert "transaction_timestamp >= %s" in query
        assert "transaction_timestamp < %s" in query
    
    def test_build_query_with_limit(self, extractor):
        """Test building query with limit."""
        query = extractor._build_query(None, None, 100)
        
        assert "LIMIT 100" in query
    
    @patch('metric_engine.data_extractor.psycopg2.pool.SimpleConnectionPool')
    def test_extract_transactions_success(self, mock_pool, extractor, sample_db_row):
        """Test successful transaction extraction."""
        # Setup mocks
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [sample_db_row]
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool_instance.putconn = Mock()
        mock_pool.return_value = mock_pool_instance
        
        extractor.connection_pool = mock_pool_instance
        
        # Execute
        transactions = extractor.extract_transactions()
        
        # Verify
        assert len(transactions) == 1
        assert transactions[0].transaction_id == "tx-123"
        mock_cursor.execute.assert_called_once()
    
    @patch('metric_engine.data_extractor.psycopg2.pool.SimpleConnectionPool')
    def test_extract_transactions_with_time_range(self, mock_pool, extractor, sample_db_row):
        """Test extraction with time range."""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [sample_db_row]
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool_instance.putconn = Mock()
        mock_pool.return_value = mock_pool_instance
        
        extractor.connection_pool = mock_pool_instance
        
        transactions = extractor.extract_transactions(start_time=start_time, end_time=end_time)
        
        assert len(transactions) == 1
        # Verify query includes time filters
        call_args = mock_cursor.execute.call_args[0][0]
        assert "transaction_timestamp >= %s" in call_args
        assert "transaction_timestamp < %s" in call_args
    
    @patch('metric_engine.data_extractor.psycopg2.pool.SimpleConnectionPool')
    def test_extract_transactions_retry_on_failure(self, mock_pool, extractor):
        """Test retry logic on extraction failure."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = [Exception("DB Error"), Exception("DB Error"), None]
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool_instance.putconn = Mock()
        mock_pool.return_value = mock_pool_instance
        
        extractor.connection_pool = mock_pool_instance
        
        # Should eventually succeed after retries
        transactions = extractor.extract_transactions()
        
        assert mock_cursor.execute.call_count == 3
    
    @patch('metric_engine.data_extractor.psycopg2.pool.SimpleConnectionPool')
    def test_extract_batch(self, mock_pool, extractor, sample_db_row):
        """Test batch extraction with offset."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [sample_db_row]
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool_instance.putconn = Mock()
        mock_pool.return_value = mock_pool_instance
        
        extractor.connection_pool = mock_pool_instance
        
        transactions = extractor.extract_batch(offset=0, limit=100)
        
        assert len(transactions) == 1
        call_args = mock_cursor.execute.call_args[0][0]
        assert "OFFSET 0" in call_args
        assert "LIMIT 100" in call_args
    
    def test_close(self, extractor):
        """Test closing connection pool."""
        mock_pool = MagicMock()
        extractor.connection_pool = mock_pool
        
        extractor.close()
        
        mock_pool.closeall.assert_called_once()
        assert extractor.connection_pool is None

