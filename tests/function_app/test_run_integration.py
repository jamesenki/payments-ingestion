"""
End-to-end integration tests for Azure Function entry point.

These tests verify the complete workflow with mocked dependencies.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from function_app.run import process_transaction_local
from function_app.parsing.models import ParsedTransaction, TransactionStatus, ParseResult


@pytest.fixture
def sample_transaction_dict():
    """Sample transaction dictionary matching simulator output."""
    return {
        "transaction_id": "test-txn-123",
        "transaction_timestamp": "2025-12-07T10:00:00Z",
        "ingestion_timestamp": None,
        "processing_timestamp": None,
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
            "user_agent": "Mozilla/5.0",
            "card_last4": "1234",
            "card_brand": "Visa"
        },
        "compliance_violations": [],
        "violation_severity": None
    }


@pytest.fixture
def mock_parsed_transaction():
    """Mock parsed transaction."""
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


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""
    
    @patch('function_app.run._get_connection_manager')
    @patch('function_app.run._get_blob_store')
    @patch('function_app.run._get_parser')
    def test_complete_workflow_success(
        self,
        mock_get_parser,
        mock_get_blob_store,
        mock_get_conn_manager,
        sample_transaction_dict,
        mock_parsed_transaction
    ):
        """Test complete successful workflow."""
        # Setup parser mock
        mock_parser = Mock()
        mock_parse_result = Mock()
        mock_parse_result.success = True
        mock_parse_result.transaction = mock_parsed_transaction
        mock_parse_result.error = None
        mock_parser.parse_and_validate.return_value = mock_parse_result
        mock_get_parser.return_value = mock_parser
        
        # Setup blob store mock
        mock_blob_store = Mock()
        mock_blob_store.store_event.return_value = "raw-events/2025/12/07/events_20251207_100000.parquet"
        mock_get_blob_store.return_value = mock_blob_store
        
        # Setup connection manager mock
        mock_conn_manager = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_manager.get_postgres_connection.return_value = mock_conn
        mock_get_conn_manager.return_value = mock_conn_manager
        
        # Process transaction
        result = process_transaction_local(sample_transaction_dict)
        
        # Assertions
        assert result["success"] is True
        assert result["transaction_id"] == "test-txn-123"
        assert result["blob_stored"] is True
        assert result["metrics_stored"] is True
        assert result["payment_metrics_updated"] is True
        assert result["histograms_updated"] is True
        assert "elapsed_ms" in result
        assert len(result["errors"]) == 0
        
        # Verify blob storage was called
        mock_blob_store.store_event.assert_called_once()
        
        # Verify database operations were called
        assert mock_cursor.execute.call_count >= 3  # dynamic_metrics, payment_metrics_5m, aggregate_histograms
        assert mock_conn.commit.call_count >= 3
        assert mock_conn_manager.release_postgres_connection.call_count >= 3
    
    @patch('function_app.run._get_parser')
    def test_workflow_validation_error(
        self,
        mock_get_parser,
        sample_transaction_dict
    ):
        """Test workflow with validation error."""
        # Setup parser to return validation error
        mock_parser = Mock()
        mock_parse_result = Mock()
        mock_parse_result.success = False
        mock_parse_result.error = Mock()
        mock_parse_result.error.constraint = "required_field"
        mock_parse_result.transaction = None
        mock_parser.parse_and_validate.return_value = mock_parse_result
        mock_get_parser.return_value = mock_parser
        
        # Process transaction
        result = process_transaction_local(sample_transaction_dict)
        
        # Assertions
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Validation error" in result["errors"][0]
    
    @patch('function_app.run._get_connection_manager')
    @patch('function_app.run._get_blob_store')
    @patch('function_app.run._get_parser')
    def test_workflow_blob_storage_failure(
        self,
        mock_get_parser,
        mock_get_blob_store,
        mock_get_conn_manager,
        sample_transaction_dict,
        mock_parsed_transaction
    ):
        """Test workflow continues when blob storage fails."""
        # Setup parser
        mock_parser = Mock()
        mock_parse_result = Mock()
        mock_parse_result.success = True
        mock_parse_result.transaction = mock_parsed_transaction
        mock_parser.parse_and_validate.return_value = mock_parse_result
        mock_get_parser.return_value = mock_parser
        
        # Setup blob store to fail
        mock_blob_store = Mock()
        mock_blob_store.store_event.return_value = None  # Indicates failure
        mock_get_blob_store.return_value = mock_blob_store
        
        # Setup connection manager
        mock_conn_manager = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn_manager.get_postgres_connection.return_value = mock_conn
        mock_get_conn_manager.return_value = mock_conn_manager
        
        # Process transaction
        result = process_transaction_local(sample_transaction_dict)
        
        # Assertions - workflow should continue even if blob storage fails
        assert result["success"] is True  # Overall success despite blob failure
        assert result["blob_stored"] is False  # Blob storage failed
        assert result["metrics_stored"] is True  # But metrics still stored
        assert result["payment_metrics_updated"] is True
        assert result["histograms_updated"] is True
    
    @patch('function_app.run._get_connection_manager')
    @patch('function_app.run._get_blob_store')
    @patch('function_app.run._get_parser')
    def test_workflow_database_failure(
        self,
        mock_get_parser,
        mock_get_blob_store,
        mock_get_conn_manager,
        sample_transaction_dict,
        mock_parsed_transaction
    ):
        """Test workflow handles database failures gracefully."""
        # Setup parser
        mock_parser = Mock()
        mock_parse_result = Mock()
        mock_parse_result.success = True
        mock_parse_result.transaction = mock_parsed_transaction
        mock_parser.parse_and_validate.return_value = mock_parse_result
        mock_get_parser.return_value = mock_parser
        
        # Setup blob store
        mock_blob_store = Mock()
        mock_blob_store.store_event.return_value = "blob/path/to/file.parquet"
        mock_get_blob_store.return_value = mock_blob_store
        
        # Setup connection manager to fail
        mock_conn_manager = Mock()
        mock_conn_manager.get_postgres_connection.side_effect = Exception("Database connection failed")
        mock_get_conn_manager.return_value = mock_conn_manager
        
        # Process transaction
        result = process_transaction_local(sample_transaction_dict)
        
        # Assertions - should handle database failure gracefully
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Processing error" in result["errors"][0]
        assert result["blob_stored"] is True  # Blob storage succeeded


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @patch('function_app.run._get_parser')
    def test_malformed_json(self, mock_get_parser):
        """Test handling of malformed JSON."""
        mock_parser = Mock()
        mock_parser.parse_and_validate.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        mock_get_parser.return_value = mock_parser
        
        result = process_transaction_local("invalid json")
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
    
    @patch('function_app.run._get_parser')
    def test_missing_required_fields(self, mock_get_parser):
        """Test handling of missing required fields."""
        mock_parser = Mock()
        mock_parse_result = Mock()
        mock_parse_result.success = False
        mock_parse_result.error = Mock()
        mock_parse_result.error.constraint = "required_field"
        mock_parser.parse_and_validate.return_value = mock_parse_result
        mock_get_parser.return_value = mock_parser
        
        incomplete_transaction = {"transaction_id": "test"}
        
        result = process_transaction_local(incomplete_transaction)
        
        assert result["success"] is False
        assert len(result["errors"]) > 0


class TestPerformance:
    """Test performance characteristics."""
    
    @patch('function_app.run._get_connection_manager')
    @patch('function_app.run._get_blob_store')
    @patch('function_app.run._get_parser')
    def test_processing_latency(
        self,
        mock_get_parser,
        mock_get_blob_store,
        mock_get_conn_manager,
        sample_transaction_dict,
        mock_parsed_transaction
    ):
        """Test that processing completes within reasonable time."""
        # Setup all mocks
        mock_parser = Mock()
        mock_parse_result = Mock()
        mock_parse_result.success = True
        mock_parse_result.transaction = mock_parsed_transaction
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
        result = process_transaction_local(sample_transaction_dict)
        
        # Assertions
        assert result["success"] is True
        assert "elapsed_ms" in result
        # Should complete in reasonable time (adjust threshold as needed)
        assert result["elapsed_ms"] < 1000  # Less than 1 second for mocked operations

