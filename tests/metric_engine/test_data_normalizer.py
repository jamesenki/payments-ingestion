"""
Unit tests for data normalizer.
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.metric_engine.data_normalizer import DataNormalizer
from src.metric_engine.models import RawTransaction, NormalizedTransaction


class TestDataNormalizer:
    """Tests for DataNormalizer."""
    
    @pytest.fixture
    def normalizer(self):
        """Create a DataNormalizer instance."""
        return DataNormalizer()
    
    def test_normalize_valid_transaction(self, normalizer, sample_raw_transaction):
        """Test normalizing a valid transaction."""
        normalized = normalizer.normalize(sample_raw_transaction)
        
        assert normalized is not None
        assert isinstance(normalized, NormalizedTransaction)
        assert normalized.transaction_id == sample_raw_transaction.transaction_id
        assert normalized.amount == sample_raw_transaction.amount
    
    def test_normalize_invalid_amount_zero(self, normalizer):
        """Test normalizing transaction with zero amount."""
        raw_tx = RawTransaction(
            transaction_id="tx-123",
            transaction_timestamp=datetime.now(),
            amount=Decimal("0.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed"
        )
        
        normalized = normalizer.normalize(raw_tx)
        assert normalized is None
    
    def test_normalize_invalid_amount_negative(self, normalizer):
        """Test normalizing transaction with negative amount."""
        raw_tx = RawTransaction(
            transaction_id="tx-123",
            transaction_timestamp=datetime.now(),
            amount=Decimal("-100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed"
        )
        
        normalized = normalizer.normalize(raw_tx)
        assert normalized is None
    
    def test_normalize_invalid_currency_short(self, normalizer):
        """Test normalizing transaction with invalid currency code."""
        raw_tx = RawTransaction(
            transaction_id="tx-123",
            transaction_timestamp=datetime.now(),
            amount=Decimal("100.00"),
            currency="US",  # Too short
            payment_method="credit_card",
            payment_status="completed"
        )
        
        normalized = normalizer.normalize(raw_tx)
        assert normalized is None
    
    def test_normalize_currency_uppercase(self, normalizer):
        """Test that currency is normalized to uppercase."""
        raw_tx = RawTransaction(
            transaction_id="tx-123",
            transaction_timestamp=datetime.now(),
            amount=Decimal("100.00"),
            currency="usd",  # Lowercase
            payment_method="credit_card",
            payment_status="completed"
        )
        
        normalized = normalizer.normalize(raw_tx)
        assert normalized is not None
        assert normalized.currency == "USD"
    
    def test_normalize_invalid_payment_status(self, normalizer):
        """Test normalizing transaction with invalid payment status."""
        raw_tx = RawTransaction(
            transaction_id="tx-123",
            transaction_timestamp=datetime.now(),
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="invalid_status"
        )
        
        normalized = normalizer.normalize(raw_tx)
        assert normalized is None
    
    def test_normalize_payment_status_lowercase(self, normalizer):
        """Test that payment status is normalized to lowercase."""
        raw_tx = RawTransaction(
            transaction_id="tx-123",
            transaction_timestamp=datetime.now(),
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="COMPLETED"  # Uppercase
        )
        
        normalized = normalizer.normalize(raw_tx)
        assert normalized is not None
        assert normalized.payment_status == "completed"
    
    def test_normalize_country_code(self, normalizer):
        """Test country code normalization."""
        raw_tx = RawTransaction(
            transaction_id="tx-123",
            transaction_timestamp=datetime.now(),
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
            customer_country="us"  # Lowercase
        )
        
        normalized = normalizer.normalize(raw_tx)
        assert normalized is not None
        assert normalized.customer_country == "US"
    
    def test_normalize_invalid_country_code(self, normalizer):
        """Test invalid country code."""
        raw_tx = RawTransaction(
            transaction_id="tx-123",
            transaction_timestamp=datetime.now(),
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
            customer_country="USA"  # Too long
        )
        
        normalized = normalizer.normalize(raw_tx)
        # Should still normalize, but country might be None or invalid
        # Depending on implementation
        assert normalized is not None
    
    def test_normalize_amount_decimal(self, normalizer):
        """Test normalizing amount from Decimal."""
        raw_tx = RawTransaction(
            transaction_id="tx-123",
            transaction_timestamp=datetime.now(),
            amount=Decimal("100.50"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed"
        )
        
        normalized = normalizer.normalize(raw_tx)
        assert normalized is not None
        assert normalized.amount == Decimal("100.50")
    
    def test_normalize_amount_float(self, normalizer):
        """Test normalizing amount from float."""
        # Create raw transaction with float amount (simulating DB return)
        raw_tx = RawTransaction(
            transaction_id="tx-123",
            transaction_timestamp=datetime.now(),
            amount=Decimal(str(100.50)),  # Convert float to Decimal
            currency="USD",
            payment_method="credit_card",
            payment_status="completed"
        )
        
        normalized = normalizer.normalize(raw_tx)
        assert normalized is not None
        assert normalized.amount == Decimal("100.50")
    
    def test_normalize_batch(self, normalizer, sample_raw_transaction):
        """Test normalizing a batch of transactions."""
        raw_transactions = [
            sample_raw_transaction,
            RawTransaction(
                transaction_id="tx-456",
                transaction_timestamp=datetime.now(),
                amount=Decimal("200.00"),
                currency="EUR",
                payment_method="debit_card",
                payment_status="completed"
            )
        ]
        
        normalized = normalizer.normalize_batch(raw_transactions)
        
        assert len(normalized) == 2
        assert all(isinstance(tx, NormalizedTransaction) for tx in normalized)
    
    def test_normalize_batch_with_invalid(self, normalizer):
        """Test normalizing batch with invalid transactions."""
        raw_transactions = [
            RawTransaction(
                transaction_id="tx-123",
                transaction_timestamp=datetime.now(),
                amount=Decimal("100.00"),
                currency="USD",
                payment_method="credit_card",
                payment_status="completed"
            ),
            RawTransaction(
                transaction_id="tx-456",
                transaction_timestamp=datetime.now(),
                amount=Decimal("0.00"),  # Invalid
                currency="USD",
                payment_method="credit_card",
                payment_status="completed"
            )
        ]
        
        normalized = normalizer.normalize_batch(raw_transactions)
        
        # Should only return valid transactions
        assert len(normalized) == 1
        assert normalized[0].transaction_id == "tx-123"

