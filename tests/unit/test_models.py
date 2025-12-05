"""
Unit tests for Transaction model.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from simulator.models import Transaction
from conftest import sample_transaction


class TestTransaction:
    """Test Transaction model."""
    
    def test_transaction_creation_minimal(self):
        """Test creating transaction with minimal fields."""
        tx = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        assert tx.amount == Decimal("100.00")
        assert tx.currency == "USD"
        assert tx.payment_method == "credit_card"
        assert tx.payment_status == "completed"
        assert tx.transaction_id is not None
        assert tx.transaction_timestamp is not None
    
    def test_transaction_creation_full(self, sample_transaction):
        """Test creating transaction with all fields."""
        assert sample_transaction.amount == Decimal("100.50")
        assert sample_transaction.currency == "USD"
        assert sample_transaction.customer_email == "test@example.com"
        assert sample_transaction.customer_country == "US"
    
    def test_transaction_defaults(self):
        """Test transaction default values."""
        tx = Transaction(
            amount=Decimal("50.00"),
            currency="EUR",
            payment_method="debit_card",
            payment_status="pending",
        )
        
        assert tx.metadata == {}
        assert tx.compliance_violations == []
        assert tx.violation_severity is None
    
    def test_transaction_currency_validation(self):
        """Test currency validation."""
        # Valid currency
        tx = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        assert tx.currency == "USD"
        
        # Invalid currency (allowed for compliance testing)
        tx = Transaction(
            amount=Decimal("100.00"),
            currency="XXX",
            payment_method="credit_card",
            payment_status="completed",
        )
        assert tx.currency == "XXX"
    
    def test_transaction_status_validation(self):
        """Test payment status validation."""
        valid_statuses = ['pending', 'completed', 'failed', 'cancelled', 'refunded']
        
        for status in valid_statuses:
            tx = Transaction(
                amount=Decimal("100.00"),
                currency="USD",
                payment_method="credit_card",
                payment_status=status,
            )
            assert tx.payment_status == status
    
    def test_transaction_country_validation(self):
        """Test country code validation."""
        # Valid 2-character country
        tx = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
            customer_country="US",
        )
        assert tx.customer_country == "US"
        
        # None is allowed
        tx = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
            customer_country=None,
        )
        assert tx.customer_country is None
    
    def test_transaction_email_validation(self):
        """Test email validation."""
        # Valid email
        tx = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
            customer_email="test@example.com",
        )
        assert tx.customer_email == "test@example.com"
        
        # Invalid email should raise ValidationError
        with pytest.raises(ValidationError):
            Transaction(
                amount=Decimal("100.00"),
                currency="USD",
                payment_method="credit_card",
                payment_status="completed",
                customer_email="invalid-email",
            )
    
    def test_transaction_to_dict(self, sample_transaction):
        """Test transaction serialization to dict."""
        tx_dict = sample_transaction.to_dict()
        
        assert isinstance(tx_dict, dict)
        assert tx_dict["transaction_id"] == "test-123"
        assert tx_dict["amount"] == 100.50
        assert tx_dict["currency"] == "USD"
        assert isinstance(tx_dict["transaction_timestamp"], str)  # ISO format
    
    def test_transaction_to_event_hub_format(self, sample_transaction):
        """Test transaction conversion to Event Hub format."""
        event_dict = sample_transaction.to_event_hub_format()
        
        assert isinstance(event_dict, dict)
        assert "transaction_id" in event_dict
        assert "amount" in event_dict
        assert "currency" in event_dict
    
    def test_transaction_with_compliance_violations(self):
        """Test transaction with compliance violations."""
        tx = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
            compliance_violations=["aml_large_amount", "kyc_missing_data"],
            violation_severity="high",
        )
        
        assert len(tx.compliance_violations) == 2
        assert tx.violation_severity == "high"
    
    def test_transaction_with_metadata(self):
        """Test transaction with metadata."""
        metadata = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
            "risk_score": 0.75,
        }
        
        tx = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
            metadata=metadata,
        )
        
        assert tx.metadata == metadata
        assert tx.metadata["risk_score"] == 0.75
    
    def test_transaction_negative_amount(self):
        """Test transaction with negative amount (for compliance testing)."""
        tx = Transaction(
            amount=Decimal("-100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        assert tx.amount == Decimal("-100.00")
    
    def test_transaction_zero_amount(self):
        """Test transaction with zero amount (for compliance testing)."""
        tx = Transaction(
            amount=Decimal("0.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        assert tx.amount == Decimal("0.00")
    
    def test_transaction_timestamp_defaults(self):
        """Test transaction timestamp defaults."""
        before = datetime.now()
        tx = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        after = datetime.now()
        
        assert before <= tx.transaction_timestamp <= after
    
    def test_transaction_custom_timestamp(self):
        """Test transaction with custom timestamp."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        tx = Transaction(
            transaction_timestamp=custom_time,
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        assert tx.transaction_timestamp == custom_time

