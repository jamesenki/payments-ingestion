"""
Integration tests for Azure Function entry point.

Tests the complete workflow:
1. Parse and validate transaction
2. Store raw event to Blob Storage
3. Store dynamic metrics to PostgreSQL
4. Update aggregate metrics
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
from uuid import uuid4

from function_app.run import (
    process_transaction_local,
    _store_raw_event_to_blob,
    _store_dynamic_metrics,
    _update_payment_metrics_5m,
    _update_aggregate_histograms,
    _route_to_dead_letter_queue,
    _extract_metrics
)
from function_app.parsing.models import ParsedTransaction, TransactionStatus
from function_app.storage.raw_event import RawEvent


@pytest.fixture
def sample_transaction():
    """Sample transaction data for testing."""
    return {
        "transaction_id": "test-txn-123",
        "transaction_timestamp": "2025-12-07T10:00:00Z",
        "amount": 100.50,
        "currency": "USD",
        "payment_method": "credit_card",
        "payment_status": "completed",
        "customer_id": "CUST-123",
        "customer_email": "test@example.com",
        "customer_country": "US",
        "merchant_id": "MERCH-456",
        "merchant_name": "Test Merchant",
        "merchant_category": "retail",
        "transaction_type": "payment",
        "channel": "web",
        "device_type": "desktop",
        "metadata": {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0"
        }
    }


@pytest.fixture
def parsed_transaction():
    """Sample parsed transaction for testing."""
    return ParsedTransaction(
        transaction_id="test-txn-123",
        correlation_id=str(uuid4()),
        timestamp=datetime(2025, 12, 7, 10, 0, 0),
        transaction_type="payment",
        channel="web",
        amount=100.50,
        currency="USD",
        merchant_id="MERCH-456",
        customer_id="CUST-123",
        status=TransactionStatus.SUCCESS,
        metadata={
            "payment_method": "credit_card",
            "payment_status": "completed"
        }
    )


class TestProcessTransactionLocal:
    """Tests for local transaction processing."""
    
    @patch('function_app.run._get_parser')
    @patch('function_app.run._get_blob_store')
    @patch('function_app.run._get_connection_manager')
    def test_process_transaction_local_success(
        self,
        mock_get_conn_manager,
        mock_get_blob_store,
        mock_get_parser,
        sample_transaction
    ):
        """Test successful transaction processing."""
        # Setup mocks
        mock_parser = Mock()
        mock_parse_result = Mock()
        mock_parse_result.success = True
        mock_parse_result.transaction = ParsedTransaction(
            transaction_id="test-txn-123",
            correlation_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            transaction_type="payment",
            channel="web",
            amount=100.50,
            currency="USD",
            merchant_id="MERCH-456",
            customer_id="CUST-123",
            status=TransactionStatus.SUCCESS,
            metadata={}
        )
        mock_parser.parse_and_validate.return_value = mock_parse_result
        mock_get_parser.return_value = mock_parser
        
        mock_blob_store = Mock()
        mock_blob_store.store_event.return_value = "blob/path/to/file.parquet"
        mock_get_blob_store.return_value = mock_blob_store
        
        mock_conn_manager = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_manager.get_postgres_connection.return_value = mock_conn
        mock_get_conn_manager.return_value = mock_conn_manager
        
        # Process transaction
        result = process_transaction_local(sample_transaction)
        
        # Assertions
        assert result["success"] is True
        assert result["transaction_id"] == "test-txn-123"
        assert result["blob_stored"] is True
        assert result["metrics_stored"] is True
        assert result["payment_metrics_updated"] is True
        assert result["histograms_updated"] is True
        assert "elapsed_ms" in result
    
    @patch('src.function_app.run._get_parser')
    def test_process_transaction_local_validation_error(
        self,
        mock_get_parser,
        sample_transaction
    ):
        """Test transaction processing with validation error."""
        # Setup mock parser to return validation error
        mock_parser = Mock()
        mock_parse_result = Mock()
        mock_parse_result.success = False
        mock_parse_result.error = Mock()
        mock_parse_result.error.constraint = "required_field"
        mock_parser.parse_and_validate.return_value = mock_parse_result
        mock_get_parser.return_value = mock_parser
        
        # Process transaction
        result = process_transaction_local(sample_transaction)
        
        # Assertions
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Validation error" in result["errors"][0]
    
    @patch('function_app.run._get_parser')
    @patch('function_app.run._get_blob_store')
    def test_process_transaction_local_processing_error(
        self,
        mock_get_blob_store,
        mock_get_parser,
        sample_transaction
    ):
        """Test transaction processing with processing error."""
        # Setup mocks
        mock_parser = Mock()
        mock_parse_result = Mock()
        mock_parse_result.success = True
        mock_parse_result.transaction = ParsedTransaction(
            transaction_id="test-txn-123",
            correlation_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            transaction_type="payment",
            channel="web",
            amount=100.50,
            currency="USD",
            merchant_id="MERCH-456",
            customer_id="CUST-123",
            status=TransactionStatus.SUCCESS,
            metadata={}
        )
        mock_parser.parse_and_validate.return_value = mock_parse_result
        mock_get_parser.return_value = mock_parser
        
        # Make blob store raise an error
        mock_blob_store = Mock()
        mock_blob_store.store_event.side_effect = Exception("Blob storage error")
        mock_get_blob_store.return_value = mock_blob_store
        
        # Process transaction
        result = process_transaction_local(sample_transaction)
        
        # Assertions
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Processing error" in result["errors"][0]


class TestStoreRawEventToBlob:
    """Tests for storing raw events to Blob Storage."""
    
    @patch('src.function_app.run._get_blob_store')
    def test_store_raw_event_success(
        self,
        mock_get_blob_store,
        parsed_transaction
    ):
        """Test successful raw event storage."""
        mock_blob_store = Mock()
        mock_blob_store.store_event.return_value = "blob/path/to/file.parquet"
        mock_get_blob_store.return_value = mock_blob_store
        
        correlation_id = uuid4()
        raw_payload = {"transaction_id": "test-txn-123"}
        
        result = _store_raw_event_to_blob(
            transaction=parsed_transaction,
            correlation_id=correlation_id,
            raw_payload=raw_payload
        )
        
        assert result == "blob/path/to/file.parquet"
        mock_blob_store.store_event.assert_called_once()
    
    @patch('src.function_app.run._get_blob_store')
    def test_store_raw_event_failure(
        self,
        mock_get_blob_store,
        parsed_transaction
    ):
        """Test raw event storage failure."""
        mock_blob_store = Mock()
        mock_blob_store.store_event.side_effect = Exception("Storage error")
        mock_get_blob_store.return_value = mock_blob_store
        
        correlation_id = uuid4()
        raw_payload = {"transaction_id": "test-txn-123"}
        
        result = _store_raw_event_to_blob(
            transaction=parsed_transaction,
            correlation_id=correlation_id,
            raw_payload=raw_payload
        )
        
        assert result is None


class TestStoreDynamicMetrics:
    """Tests for storing dynamic metrics."""
    
    @patch('function_app.run._get_connection_manager')
    def test_store_dynamic_metrics_success(
        self,
        mock_get_conn_manager,
        parsed_transaction
    ):
        """Test successful dynamic metrics storage."""
        mock_conn_manager = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_manager.get_postgres_connection.return_value = mock_conn
        mock_get_conn_manager.return_value = mock_conn_manager
        
        correlation_id = uuid4()
        metrics = [
            {
                "metric_type": "transaction_amount",
                "metric_value": 100.50,
                "metric_data": {"currency": "USD"}
            }
        ]
        
        result = _store_dynamic_metrics(
            transaction=parsed_transaction,
            correlation_id=correlation_id,
            metrics=metrics
        )
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called_once()
        mock_conn_manager.release_postgres_connection.assert_called_once_with(mock_conn)
    
    @patch('function_app.run._get_connection_manager')
    def test_store_dynamic_metrics_failure(
        self,
        mock_get_conn_manager,
        parsed_transaction
    ):
        """Test dynamic metrics storage failure."""
        mock_conn_manager = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_manager.get_postgres_connection.return_value = mock_conn
        mock_get_conn_manager.return_value = mock_conn_manager
        
        correlation_id = uuid4()
        metrics = [{"metric_type": "test", "metric_value": 1}]
        
        result = _store_dynamic_metrics(
            transaction=parsed_transaction,
            correlation_id=correlation_id,
            metrics=metrics
        )
        
        assert result is False


class TestUpdatePaymentMetrics5m:
    """Tests for updating payment_metrics_5m table."""
    
    @patch('function_app.run._get_connection_manager')
    def test_update_payment_metrics_5m_success(
        self,
        mock_get_conn_manager,
        parsed_transaction
    ):
        """Test successful payment metrics update."""
        mock_conn_manager = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_manager.get_postgres_connection.return_value = mock_conn
        mock_get_conn_manager.return_value = mock_conn_manager
        
        result = _update_payment_metrics_5m(parsed_transaction)
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called_once()


class TestExtractMetrics:
    """Tests for metric extraction."""
    
    def test_extract_metrics(self, parsed_transaction):
        """Test metric extraction from transaction."""
        metrics = _extract_metrics(parsed_transaction)
        
        assert len(metrics) == 3
        assert any(m["metric_type"] == "transaction_amount" for m in metrics)
        assert any(m["metric_type"] == "channel_usage" for m in metrics)
        assert any(m["metric_type"] == "transaction_status" for m in metrics)


class TestRouteToDeadLetterQueue:
    """Tests for dead-letter queue routing."""
    
    @patch('function_app.run._get_connection_manager')
    def test_route_to_dead_letter_queue_success(
        self,
        mock_get_conn_manager
    ):
        """Test successful routing to dead-letter queue."""
        mock_conn_manager = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_manager.get_postgres_connection.return_value = mock_conn
        mock_get_conn_manager.return_value = mock_conn_manager
        
        correlation_id = uuid4()
        raw_payload = {"transaction_id": "test-txn-123"}
        
        result = _route_to_dead_letter_queue(
            transaction_id="test-txn-123",
            correlation_id=correlation_id,
            error_type="validation_error",
            error_message="Test error",
            raw_payload=raw_payload
        )
        
        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

