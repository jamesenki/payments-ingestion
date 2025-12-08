"""
Unit tests for DataParser.

Tests WO-38: Build Data Parser and Validation Engine with Schema Support
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from src.function_app.parsing.data_parser import DataParser
from src.function_app.parsing.models import (
    ParsedTransaction,
    TransactionStatus,
    ValidationError,
    ParseResult,
    FailedMessage
)


class TestDataParser:
    """Tests for DataParser class."""
    
    def test_parser_initialization(self):
        """Test DataParser initialization."""
        parser = DataParser()
        assert parser is not None
        assert parser.parser is not None
        assert parser.dead_letter_handler is None
        assert parser._metrics["total_processed"] == 0
    
    def test_parser_initialization_with_dead_letter_handler(self):
        """Test DataParser initialization with dead-letter handler."""
        handler = Mock()
        parser = DataParser(dead_letter_handler=handler)
        assert parser.dead_letter_handler == handler
    
    def test_parse_and_validate_valid_transaction(self):
        """Test parsing a valid transaction."""
        parser = DataParser()
        transaction_data = {
            "transaction_id": "tx-123",
            "correlation_id": "corr-456",
            "timestamp": "2025-01-01T12:00:00Z",
            "transaction_type": "payment",
            "channel": "web",
            "amount": 100.0,
            "currency": "USD",
            "merchant_id": "merchant-1",
            "customer_id": "customer-1",
            "status": "success"
        }
        
        result = parser.parse_and_validate(json.dumps(transaction_data))
        
        assert result.success is True
        assert result.transaction is not None
        assert parser._metrics["successful"] == 1
        assert parser._metrics["total_processed"] == 1
    
    def test_parse_and_validate_invalid_transaction(self):
        """Test parsing an invalid transaction."""
        parser = DataParser()
        invalid_data = '{"transaction_id": "tx-123"}'  # Missing required fields
        
        result = parser.parse_and_validate(invalid_data)
        
        assert result.success is False
        assert parser._metrics["failed"] == 1
        assert parser._metrics["total_processed"] == 1
    
    def test_parse_and_validate_metrics_tracking(self):
        """Test that metrics are tracked correctly."""
        parser = DataParser()
        
        # Parse valid transaction
        valid_data = {
            "transaction_id": "tx-1",
            "correlation_id": "corr-1",
            "timestamp": "2025-01-01T12:00:00Z",
            "transaction_type": "payment",
            "channel": "web",
            "amount": 100.0,
            "currency": "USD",
            "merchant_id": "merchant-1",
            "customer_id": "customer-1",
            "status": "success"
        }
        parser.parse_and_validate(json.dumps(valid_data))
        
        # Parse invalid transaction
        parser.parse_and_validate('{"invalid": "data"}')
        
        metrics = parser.get_metrics()
        assert metrics["total_processed"] == 2
        assert metrics["successful"] == 1
        assert metrics["failed"] == 1
        assert metrics["success_rate"] == 50.0
    
    def test_parse_and_validate_dead_letter_routing(self):
        """Test that failed messages are routed to dead-letter queue."""
        handler = Mock()
        parser = DataParser(dead_letter_handler=handler)
        invalid_data = '{"transaction_id": "tx-123"}'  # Missing required fields
        
        result = parser.parse_and_validate(invalid_data)
        
        assert result.success is False
        # Dead-letter handler should be called
        assert handler.called
        call_args = handler.call_args[0][0]
        assert isinstance(call_args, FailedMessage)
        assert call_args.failure_reason is not None
    
    def test_parse_and_validate_no_dead_letter_handler(self):
        """Test that parser works without dead-letter handler."""
        parser = DataParser(dead_letter_handler=None)
        invalid_data = '{"transaction_id": "tx-123"}'
        
        # Should not raise error even without handler
        result = parser.parse_and_validate(invalid_data)
        assert result.success is False
    
    def test_parse_batch(self):
        """Test parsing a batch of messages."""
        parser = DataParser()
        messages = [
            json.dumps({
                "transaction_id": f"tx-{i}",
                "correlation_id": f"corr-{i}",
                "timestamp": "2025-01-01T12:00:00Z",
                "transaction_type": "payment",
                "channel": "web",
                "amount": 100.0 + i,
                "currency": "USD",
                "merchant_id": "merchant-1",
                "customer_id": "customer-1",
                "status": "success"
            })
            for i in range(5)
        ]
        
        results = parser.parse_batch(messages)
        
        assert len(results) == 5
        assert all(r.success for r in results)
        assert parser._metrics["total_processed"] == 5
        assert parser._metrics["successful"] == 5
    
    def test_parse_batch_with_failures(self):
        """Test parsing batch with some failures."""
        parser = DataParser()
        messages = [
            json.dumps({
                "transaction_id": "tx-1",
                "correlation_id": "corr-1",
                "timestamp": "2025-01-01T12:00:00Z",
                "transaction_type": "payment",
                "channel": "web",
                "amount": 100.0,
                "currency": "USD",
                "merchant_id": "merchant-1",
                "customer_id": "customer-1",
                "status": "success"
            }),
            '{"invalid": "data"}',  # Invalid message
            json.dumps({
                "transaction_id": "tx-3",
                "correlation_id": "corr-3",
                "timestamp": "2025-01-01T12:00:00Z",
                "transaction_type": "payment",
                "channel": "web",
                "amount": 100.0,
                "currency": "USD",
                "merchant_id": "merchant-1",
                "customer_id": "customer-1",
                "status": "success"
            })
        ]
        
        results = parser.parse_batch(messages)
        
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True
        assert parser._metrics["successful"] == 2
        assert parser._metrics["failed"] == 1
    
    def test_get_metrics(self):
        """Test getting validation metrics."""
        parser = DataParser()
        
        # Process some messages
        valid_data = {
            "transaction_id": "tx-1",
            "correlation_id": "corr-1",
            "timestamp": "2025-01-01T12:00:00Z",
            "transaction_type": "payment",
            "channel": "web",
            "amount": 100.0,
            "currency": "USD",
            "merchant_id": "merchant-1",
            "customer_id": "customer-1",
            "status": "success"
        }
        parser.parse_and_validate(json.dumps(valid_data))
        parser.parse_and_validate('{"invalid": "data"}')
        
        metrics = parser.get_metrics()
        
        assert "total_processed" in metrics
        assert "successful" in metrics
        assert "failed" in metrics
        assert "failed_by_type" in metrics
        assert "avg_processing_time_ms" in metrics
        assert "success_rate" in metrics
        assert metrics["total_processed"] == 2
        assert metrics["successful"] == 1
        assert metrics["failed"] == 1
    
    def test_reset_metrics(self):
        """Test resetting validation metrics."""
        parser = DataParser()
        
        # Process some messages
        valid_data = {
            "transaction_id": "tx-1",
            "correlation_id": "corr-1",
            "timestamp": "2025-01-01T12:00:00Z",
            "transaction_type": "payment",
            "channel": "web",
            "amount": 100.0,
            "currency": "USD",
            "merchant_id": "merchant-1",
            "customer_id": "customer-1",
            "status": "success"
        }
        parser.parse_and_validate(json.dumps(valid_data))
        
        assert parser._metrics["total_processed"] == 1
        
        parser.reset_metrics()
        
        assert parser._metrics["total_processed"] == 0
        assert parser._metrics["successful"] == 0
        assert parser._metrics["failed"] == 0
    
    def test_reload_schemas(self):
        """Test reloading schemas (hot-reload support)."""
        parser = DataParser()
        
        # Add a schema to cache
        parser._schemas["test_schema"] = {"field": "value"}
        
        count = parser.reload_schemas()
        
        assert count == 1
        assert len(parser._schemas) == 0
    
    def test_failed_by_type_tracking(self):
        """Test that failures are tracked by error type."""
        parser = DataParser()
        
        # Parse invalid messages with different error types
        parser.parse_and_validate('{"transaction_id": "tx-1"}')  # Missing fields
        parser.parse_and_validate('{"invalid": "json"')  # Invalid JSON
        
        metrics = parser.get_metrics()
        assert metrics["failed"] == 2
        assert len(metrics["failed_by_type"]) > 0
    
    def test_dead_letter_handler_exception_handling(self):
        """Test that dead-letter handler exceptions don't break parsing."""
        def failing_handler(failed_message):
            raise RuntimeError("Handler failed")
        
        parser = DataParser(dead_letter_handler=failing_handler)
        invalid_data = '{"transaction_id": "tx-123"}'
        
        # Should not raise exception even if handler fails
        result = parser.parse_and_validate(invalid_data)
        assert result.success is False
        # Metrics should still be updated
        assert parser._metrics["failed"] == 1

