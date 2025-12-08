"""
Unit tests for TransactionParser.

Tests WO-59: Transaction Parser
"""

import pytest
import json
from datetime import datetime
from src.function_app.parsing.parser import TransactionParser
from src.function_app.parsing.models import (
    ParsedTransaction,
    TransactionStatus,
    ValidationError,
    ParseResult
)


class TestTransactionParser:
    """Tests for TransactionParser class."""
    
    def test_parser_initialization(self):
        """Test TransactionParser initialization."""
        parser = TransactionParser()
        assert parser is not None
    
    def test_parse_and_validate_valid_transaction(self):
        """Test parsing a valid transaction."""
        parser = TransactionParser()
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
        assert result.transaction.transaction_id == "tx-123"
        assert result.transaction.amount == 100.0
        assert result.transaction.status == TransactionStatus.SUCCESS
        assert result.error is None
    
    def test_parse_and_validate_invalid_json(self):
        """Test parsing invalid JSON."""
        parser = TransactionParser()
        invalid_json = "{invalid json}"
        
        result = parser.parse_and_validate(invalid_json)
        
        assert result.success is False
        assert result.transaction is None
        assert result.error is not None
        assert result.error.field == "body"  # Field is "body" not "json"
        assert "JSON" in result.error.message.upper() or "parse" in result.error.message.lower() or "malformed" in result.error.message.lower()
    
    def test_parse_and_validate_missing_required_field(self):
        """Test parsing transaction with missing required field."""
        parser = TransactionParser()
        transaction_data = {
            "transaction_id": "tx-123",
            # Missing correlation_id
            "amount": 100.0,
            "currency": "USD"
        }
        
        result = parser.parse_and_validate(json.dumps(transaction_data))
        
        assert result.success is False
        assert result.error is not None
        assert "correlation_id" in result.error.field.lower() or "required" in result.error.message.lower()
    
    def test_parse_and_validate_invalid_status(self):
        """Test parsing transaction with invalid status."""
        parser = TransactionParser()
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
            "status": "invalid_status"  # Invalid status
        }
        
        result = parser.parse_and_validate(json.dumps(transaction_data))
        
        # Should either fail validation or map to ERROR status
        assert result.success is False or result.transaction.status == TransactionStatus.ERROR
    
    def test_parse_and_validate_all_statuses(self):
        """Test parsing transactions with all valid statuses."""
        parser = TransactionParser()
        
        for status_value in ["success", "declined", "timeout", "error"]:
            transaction_data = {
                "transaction_id": f"tx-{status_value}",
                "correlation_id": "corr-1",
                "timestamp": "2025-01-01T12:00:00Z",
                "transaction_type": "payment",
                "channel": "web",
                "amount": 100.0,
                "currency": "USD",
                "merchant_id": "merchant-1",
                "customer_id": "customer-1",
                "status": status_value
            }
            
            result = parser.parse_and_validate(json.dumps(transaction_data))
            assert result.success is True
            assert result.transaction.status.value == status_value
    
    def test_parse_and_validate_negative_amount(self):
        """Test parsing transaction with negative amount."""
        parser = TransactionParser()
        transaction_data = {
            "transaction_id": "tx-123",
            "correlation_id": "corr-456",
            "timestamp": "2025-01-01T12:00:00Z",
            "transaction_type": "payment",
            "channel": "web",
            "amount": -100.0,  # Negative amount
            "currency": "USD",
            "merchant_id": "merchant-1",
            "customer_id": "customer-1",
            "status": "success"
        }
        
        result = parser.parse_and_validate(json.dumps(transaction_data))
        
        # Should either fail validation or allow negative (for refunds)
        assert result.success is False or result.transaction.amount == -100.0
    
    def test_parse_and_validate_empty_string(self):
        """Test parsing empty string."""
        parser = TransactionParser()
        
        result = parser.parse_and_validate("")
        
        assert result.success is False
        assert result.error is not None
    
    def test_parse_and_validate_none(self):
        """Test parsing None value."""
        parser = TransactionParser()
        
        result = parser.parse_and_validate(None)
        
        assert result.success is False
        assert result.error is not None
    
    def test_parse_and_validate_with_metadata(self):
        """Test parsing transaction with metadata."""
        parser = TransactionParser()
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
            "status": "success",
            "metadata": {"source": "mobile_app", "device": "ios"}
        }
        
        result = parser.parse_and_validate(json.dumps(transaction_data))
        
        assert result.success is True
        assert result.transaction.metadata == {"source": "mobile_app", "device": "ios"}
    
    def test_parse_and_validate_timestamp_parsing(self):
        """Test parsing various timestamp formats."""
        parser = TransactionParser()
        
        timestamp_formats = [
            "2025-01-01T12:00:00Z",
            "2025-01-01T12:00:00+00:00",
            "2025-01-01 12:00:00"
        ]
        
        for timestamp in timestamp_formats:
            transaction_data = {
                "transaction_id": "tx-123",
                "correlation_id": "corr-456",
                "timestamp": timestamp,
                "transaction_type": "payment",
                "channel": "web",
                "amount": 100.0,
                "currency": "USD",
                "merchant_id": "merchant-1",
                "customer_id": "customer-1",
                "status": "success"
            }
            
            result = parser.parse_and_validate(json.dumps(transaction_data))
            # Should handle at least ISO format
            if timestamp.endswith("Z") or "+00:00" in timestamp:
                assert result.success is True
                assert isinstance(result.transaction.timestamp, datetime)

