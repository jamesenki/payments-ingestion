"""
Unit tests for TransactionGenerator.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from simulator.transaction_generator import TransactionGenerator
from simulator.config.schema import TransactionConfig, VariabilityConfig
from conftest import minimal_transaction_config, full_transaction_config


class TestTransactionGenerator:
    """Test TransactionGenerator class."""
    
    def test_initialization(self, minimal_transaction_config):
        """Test generator initialization."""
        generator = TransactionGenerator(minimal_transaction_config)
        
        assert generator.config == minimal_transaction_config
        assert generator.variability is not None
        assert generator.faker is not None
    
    def test_prepare_weighted_choices(self, minimal_transaction_config):
        """Test weighted choices preparation."""
        generator = TransactionGenerator(minimal_transaction_config)
        
        distribution = {"a": 0.5, "b": 0.3, "c": 0.2}
        choices = generator._prepare_weighted_choices(distribution)
        
        assert len(choices) == 3
        assert ("a", 0.5) in choices
    
    def test_weighted_choice(self, minimal_transaction_config):
        """Test weighted choice selection."""
        generator = TransactionGenerator(minimal_transaction_config)
        
        choices = [("a", 0.5), ("b", 0.3), ("c", 0.2)]
        result = generator._weighted_choice(choices)
        
        assert result in ["a", "b", "c"]
    
    def test_generate_amount_normal_distribution(self, full_transaction_config):
        """Test amount generation with normal distribution."""
        generator = TransactionGenerator(full_transaction_config)
        amounts = [generator.generate_amount() for _ in range(100)]
        
        assert all(1.0 <= float(amt) <= 1000.0 for amt in amounts)
        assert all(isinstance(amt, Decimal) for amt in amounts)
    
    def test_generate_amount_uniform_distribution(self, minimal_transaction_config):
        """Test amount generation with uniform distribution."""
        config = TransactionConfig(
            volume={"total": 100, "rate": 10},
            variability=VariabilityConfig(
                amounts={
                    "distribution": "uniform",
                    "min": 10.0,
                    "max": 100.0,
                }
            )
        )
        generator = TransactionGenerator(config)
        amounts = [generator.generate_amount() for _ in range(50)]
        
        assert all(10.0 <= float(amt) <= 100.0 for amt in amounts)
    
    def test_generate_amount_exponential_distribution(self, minimal_transaction_config):
        """Test amount generation with exponential distribution."""
        config = TransactionConfig(
            volume={"total": 100, "rate": 10},
            variability=VariabilityConfig(
                amounts={
                    "distribution": "exponential",
                    "min": 1.0,
                    "max": 1000.0,
                }
            )
        )
        generator = TransactionGenerator(config)
        amounts = [generator.generate_amount() for _ in range(50)]
        
        assert all(1.0 <= float(amt) <= 1000.0 for amt in amounts)
    
    def test_generate_amount_bimodal_distribution(self, minimal_transaction_config):
        """Test amount generation with bimodal distribution."""
        config = TransactionConfig(
            volume={"total": 100, "rate": 10},
            variability=VariabilityConfig(
                amounts={
                    "distribution": "bimodal",
                    "mean": 100.0,
                    "std_dev": 50.0,
                    "min": 1.0,
                    "max": 1000.0,
                    "bimodal_peaks": [50.0, 500.0],
                }
            )
        )
        generator = TransactionGenerator(config)
        amounts = [generator.generate_amount() for _ in range(50)]
        
        assert all(1.0 <= float(amt) <= 1000.0 for amt in amounts)
    
    def test_generate_timestamp(self, minimal_transaction_config):
        """Test timestamp generation."""
        generator = TransactionGenerator(minimal_transaction_config)
        timestamp = generator.generate_timestamp()
        
        assert isinstance(timestamp, datetime)
        # Timestamp should be within next 7 days (allow some margin)
        now = datetime.now()
        max_future = now + timedelta(days=8)  # Allow 8 days for safety
        min_past = now - timedelta(seconds=1)  # Allow 1 second in past for edge cases
        assert min_past <= timestamp <= max_future
    
    def test_generate_customer_data(self, minimal_transaction_config):
        """Test customer data generation."""
        generator = TransactionGenerator(minimal_transaction_config)
        customer_data = generator.generate_customer_data("US")
        
        assert "customer_id" in customer_data
        assert "customer_email" in customer_data
        assert customer_data["customer_country"] == "US"
    
    def test_generate_merchant_data(self, minimal_transaction_config):
        """Test merchant data generation."""
        generator = TransactionGenerator(minimal_transaction_config)
        merchant_data = generator.generate_merchant_data("retail")
        
        assert "merchant_id" in merchant_data
        assert "merchant_name" in merchant_data
        assert merchant_data["merchant_category"] == "retail"
    
    def test_generate_transaction(self, minimal_transaction_config):
        """Test single transaction generation."""
        generator = TransactionGenerator(minimal_transaction_config)
        transaction = generator.generate_transaction()
        
        assert transaction is not None
        assert transaction.transaction_id is not None
        assert transaction.amount > 0
        assert transaction.currency is not None
        assert transaction.payment_method is not None
        assert transaction.payment_status is not None
    
    def test_generate_batch(self, minimal_transaction_config):
        """Test batch transaction generation."""
        generator = TransactionGenerator(minimal_transaction_config)
        transactions = generator.generate_batch(10)
        
        assert len(transactions) == 10
        assert all(tx is not None for tx in transactions)
    
    def test_generate_transaction_with_metadata(self, minimal_transaction_config):
        """Test transaction generation with metadata."""
        generator = TransactionGenerator(minimal_transaction_config)
        
        metadata_config = {
            "include_ip_address": True,
            "include_user_agent": True,
            "include_risk_score": True,
        }
        
        transaction = generator.generate_transaction(metadata_config)
        
        assert "ip_address" in transaction.metadata
        assert "user_agent" in transaction.metadata
        assert "risk_score" in transaction.metadata
    
    def test_payment_method_distribution(self, minimal_transaction_config):
        """Test payment method distribution."""
        config = TransactionConfig(
            volume={"total": 100, "rate": 10},
            variability=VariabilityConfig(
                payment_methods={
                    "credit_card": 1.0,  # 100% credit card
                }
            )
        )
        generator = TransactionGenerator(config)
        
        transactions = generator.generate_batch(50)
        all_credit = all(tx.payment_method == "credit_card" for tx in transactions)
        
        assert all_credit
    
    def test_currency_distribution(self, minimal_transaction_config):
        """Test currency distribution."""
        config = TransactionConfig(
            volume={"total": 100, "rate": 10},
            variability=VariabilityConfig(
                currencies={
                    "USD": 1.0,  # 100% USD
                }
            )
        )
        generator = TransactionGenerator(config)
        
        transactions = generator.generate_batch(50)
        all_usd = all(tx.currency == "USD" for tx in transactions)
        
        assert all_usd
    
    def test_country_handling_other(self, minimal_transaction_config):
        """Test handling of 'other' country."""
        generator = TransactionGenerator(minimal_transaction_config)
        
        # Generate multiple transactions to potentially hit 'other'
        transactions = generator.generate_batch(100)
        
        # All should have valid 2-character country codes
        countries = [tx.customer_country for tx in transactions if tx.customer_country]
        assert all(len(c) == 2 for c in countries)

