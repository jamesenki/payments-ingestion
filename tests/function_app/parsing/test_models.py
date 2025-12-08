"""
Unit tests for parsing data models.

Tests WO-35: Core Data Models for Transaction Parsing
"""

import pytest
from datetime import datetime
from src.function_app.parsing.models import (
    TransactionStatus,
    ParsedTransaction,
    ValidationError,
    ParseResult,
    FailedMessage
)


class TestTransactionStatus:
    """Tests for TransactionStatus enum."""
    
    def test_status_values(self):
        """Test all status enum values."""
        assert TransactionStatus.SUCCESS.value == "success"
        assert TransactionStatus.DECLINED.value == "declined"
        assert TransactionStatus.TIMEOUT.value == "timeout"
        assert TransactionStatus.ERROR.value == "error"
    
    def test_status_str(self):
        """Test __str__ method returns value."""
        assert str(TransactionStatus.SUCCESS) == "success"
        assert str(TransactionStatus.DECLINED) == "declined"
    
    def test_status_comparison(self):
        """Test status enum comparison."""
        assert TransactionStatus.SUCCESS == TransactionStatus.SUCCESS
        assert TransactionStatus.SUCCESS != TransactionStatus.DECLINED


class TestParsedTransaction:
    """Tests for ParsedTransaction dataclass."""
    
    def test_parsed_transaction_creation(self):
        """Test basic ParsedTransaction creation."""
        tx = ParsedTransaction(
            transaction_id="tx-123",
            correlation_id="corr-456",
            timestamp=datetime.utcnow(),
            transaction_type="payment",
            channel="web",
            amount=100.0,
            currency="USD",
            merchant_id="merchant-1",
            customer_id="customer-1",
            status=TransactionStatus.SUCCESS
        )
        
        assert tx.transaction_id == "tx-123"
        assert tx.correlation_id == "corr-456"
        assert tx.transaction_type == "payment"
        assert tx.channel == "web"
        assert tx.amount == 100.0
        assert tx.currency == "USD"
        assert tx.merchant_id == "merchant-1"
        assert tx.customer_id == "customer-1"
        assert tx.status == TransactionStatus.SUCCESS
        assert tx.metadata == {}
    
    def test_parsed_transaction_with_metadata(self):
        """Test ParsedTransaction with metadata."""
        metadata = {"source": "mobile_app", "device": "ios"}
        tx = ParsedTransaction(
            transaction_id="tx-1",
            correlation_id="corr-1",
            timestamp=datetime.utcnow(),
            transaction_type="payment",
            channel="mobile",
            amount=50.0,
            currency="EUR",
            merchant_id="merchant-1",
            customer_id="customer-1",
            status=TransactionStatus.SUCCESS,
            metadata=metadata
        )
        
        assert tx.metadata == metadata
    
    def test_parsed_transaction_to_dict(self):
        """Test to_dict() method."""
        tx = ParsedTransaction(
            transaction_id="tx-123",
            correlation_id="corr-456",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            transaction_type="payment",
            channel="web",
            amount=100.0,
            currency="USD",
            merchant_id="merchant-1",
            customer_id="customer-1",
            status=TransactionStatus.SUCCESS,
            metadata={"key": "value"}
        )
        
        data = tx.to_dict()
        
        assert data["transaction_id"] == "tx-123"
        assert data["correlation_id"] == "corr-456"
        assert data["timestamp"] == "2025-01-01T12:00:00"
        assert data["transaction_type"] == "payment"
        assert data["channel"] == "web"
        assert data["amount"] == 100.0
        assert data["currency"] == "USD"
        assert data["merchant_id"] == "merchant-1"
        assert data["customer_id"] == "customer-1"
        assert data["status"] == "success"  # Enum value as string
        assert data["metadata"] == {"key": "value"}
    
    def test_parsed_transaction_all_statuses(self):
        """Test ParsedTransaction with all status types."""
        for status in TransactionStatus:
            tx = ParsedTransaction(
                transaction_id=f"tx-{status.value}",
                correlation_id="corr-1",
                timestamp=datetime.utcnow(),
                transaction_type="payment",
                channel="web",
                amount=100.0,
                currency="USD",
                merchant_id="merchant-1",
                customer_id="customer-1",
                status=status
            )
            assert tx.status == status
            assert tx.to_dict()["status"] == status.value


class TestValidationError:
    """Tests for ValidationError dataclass."""
    
    def test_validation_error_creation(self):
        """Test basic ValidationError creation."""
        error = ValidationError(
            field="amount",
            constraint="range",
            expected="0.01 to 10000.00",
            actual=-10.0,
            message="Amount must be positive"
        )
        
        assert error.field == "amount"
        assert error.constraint == "range"
        assert error.expected == "0.01 to 10000.00"
        assert error.actual == -10.0
        assert error.message == "Amount must be positive"
    
    def test_validation_error_to_dict(self):
        """Test to_dict() method."""
        error = ValidationError(
            field="currency",
            constraint="required",
            expected="ISO 4217 code",
            actual=None,
            message="Currency is required"
        )
        
        data = error.to_dict()
        
        assert data["field"] == "currency"
        assert data["constraint"] == "required"
        assert data["expected"] == "ISO 4217 code"
        assert data["actual"] is None
        assert data["message"] == "Currency is required"


class TestParseResult:
    """Tests for ParseResult dataclass."""
    
    def test_parse_result_success_creation(self):
        """Test creating successful ParseResult."""
        tx = ParsedTransaction(
            transaction_id="tx-123",
            correlation_id="corr-456",
            timestamp=datetime.utcnow(),
            transaction_type="payment",
            channel="web",
            amount=100.0,
            currency="USD",
            merchant_id="merchant-1",
            customer_id="customer-1",
            status=TransactionStatus.SUCCESS
        )
        
        result = ParseResult.success_result(tx, raw_message='{"amount": 100.0}')
        
        assert result.success is True
        assert result.transaction == tx
        assert result.error is None
        assert result.raw_message == '{"amount": 100.0}'
    
    def test_parse_result_error_creation(self):
        """Test creating failed ParseResult."""
        error = ValidationError(
            field="amount",
            constraint="type",
            expected="float",
            actual="string",
            message="Amount must be a number"
        )
        
        result = ParseResult.error_result(error, raw_message='{"amount": "invalid"}')
        
        assert result.success is False
        assert result.transaction is None
        assert result.error == error
        assert result.raw_message == '{"amount": "invalid"}'
    
    def test_parse_result_success_without_raw_message(self):
        """Test success_result without raw_message."""
        tx = ParsedTransaction(
            transaction_id="tx-1",
            correlation_id="corr-1",
            timestamp=datetime.utcnow(),
            transaction_type="payment",
            channel="web",
            amount=100.0,
            currency="USD",
            merchant_id="merchant-1",
            customer_id="customer-1",
            status=TransactionStatus.SUCCESS
        )
        
        result = ParseResult.success_result(tx)
        
        assert result.success is True
        assert result.transaction == tx
        assert result.raw_message is None
    
    def test_parse_result_error_without_raw_message(self):
        """Test error_result without raw_message."""
        error = ValidationError(
            field="currency",
            constraint="required",
            expected="ISO 4217 code",
            actual=None,
            message="Currency is required"
        )
        
        result = ParseResult.error_result(error)
        
        assert result.success is False
        assert result.error == error
        assert result.raw_message is None
    
    def test_parse_result_to_dict_success(self):
        """Test to_dict() for successful result."""
        tx = ParsedTransaction(
            transaction_id="tx-123",
            correlation_id="corr-456",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            transaction_type="payment",
            channel="web",
            amount=100.0,
            currency="USD",
            merchant_id="merchant-1",
            customer_id="customer-1",
            status=TransactionStatus.SUCCESS
        )
        
        result = ParseResult.success_result(tx, raw_message='{"amount": 100.0}')
        data = result.to_dict()
        
        assert data["success"] is True
        assert "transaction" in data
        assert data["transaction"]["transaction_id"] == "tx-123"
        assert "error" not in data
        assert data["raw_message"] == '{"amount": 100.0}'
    
    def test_parse_result_to_dict_error(self):
        """Test to_dict() for error result."""
        error = ValidationError(
            field="amount",
            constraint="range",
            expected="positive number",
            actual=-10.0,
            message="Amount must be positive"
        )
        
        result = ParseResult.error_result(error, raw_message='{"amount": -10.0}')
        data = result.to_dict()
        
        assert data["success"] is False
        assert "transaction" not in data
        assert "error" in data
        assert data["error"]["field"] == "amount"
        assert data["raw_message"] == '{"amount": -10.0}'
    
    def test_parse_result_to_dict_no_raw_message(self):
        """Test to_dict() when raw_message is None."""
        tx = ParsedTransaction(
            transaction_id="tx-1",
            correlation_id="corr-1",
            timestamp=datetime.utcnow(),
            transaction_type="payment",
            channel="web",
            amount=100.0,
            currency="USD",
            merchant_id="merchant-1",
            customer_id="customer-1",
            status=TransactionStatus.SUCCESS
        )
        
        result = ParseResult.success_result(tx)
        data = result.to_dict()
        
        assert data["raw_message"] is None


class TestFailedMessage:
    """Tests for FailedMessage dataclass."""
    
    def test_failed_message_creation(self):
        """Test basic FailedMessage creation."""
        failed = FailedMessage(
            failure_reason="parse_error",
            raw_message='{"invalid": json}',
            timestamp=datetime.utcnow(),
            transaction_id="tx-123",
            correlation_id="corr-456",
            failure_details={"error": "JSON decode error"}
        )
        
        assert failed.failure_reason == "parse_error"
        assert failed.raw_message == '{"invalid": json}'
        assert isinstance(failed.timestamp, datetime)
        assert failed.transaction_id == "tx-123"
        assert failed.correlation_id == "corr-456"
        assert failed.failure_details == {"error": "JSON decode error"}
    
    def test_failed_message_with_defaults(self):
        """Test FailedMessage with default values."""
        failed = FailedMessage(
            failure_reason="validation_error",
            raw_message='{"amount": -10.0}',
            timestamp=datetime.utcnow()
        )
        
        assert failed.failure_reason == "validation_error"
        assert failed.transaction_id is None
        assert failed.correlation_id is None
        assert failed.failure_details == {}
    
    def test_failed_message_to_dict(self):
        """Test to_dict() method."""
        failed = FailedMessage(
            failure_reason="parse_error",
            raw_message='{"invalid": json}',
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            transaction_id="tx-123",
            correlation_id="corr-456",
            failure_details={"error": "JSON decode error", "line": 1}
        )
        
        data = failed.to_dict()
        
        assert data["transaction_id"] == "tx-123"
        assert data["correlation_id"] == "corr-456"
        assert data["failure_reason"] == "parse_error"
        assert data["failure_details"] == {"error": "JSON decode error", "line": 1}
        assert data["raw_message"] == '{"invalid": json}'
        assert data["timestamp"] == "2025-01-01T12:00:00"
    
    def test_failed_message_to_dict_with_none_ids(self):
        """Test to_dict() when transaction_id and correlation_id are None."""
        failed = FailedMessage(
            failure_reason="unknown_error",
            raw_message="unknown",
            timestamp=datetime.utcnow()
        )
        
        data = failed.to_dict()
        
        assert data["transaction_id"] is None
        assert data["correlation_id"] is None
        assert data["failure_reason"] == "unknown_error"

