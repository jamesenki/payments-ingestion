"""
Unit tests for metric engine models.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from decimal import Decimal
from datetime import datetime
from pydantic import ValidationError

from src.metric_engine.models import (
    RawTransaction,
    NormalizedTransaction,
    DerivedMetric,
    AggregatedMetric,
    Cluster,
    TimeWindow
)


class TestRawTransaction:
    """Tests for RawTransaction model."""
    
    def test_valid_raw_transaction(self, sample_raw_transaction):
        """Test creating a valid raw transaction."""
        assert sample_raw_transaction.transaction_id == "tx-123"
        assert sample_raw_transaction.amount == Decimal("100.50")
        assert sample_raw_transaction.currency == "USD"
    
    def test_raw_transaction_with_optional_fields(self):
        """Test raw transaction with optional fields."""
        tx = RawTransaction(
            transaction_id="tx-456",
            transaction_timestamp=datetime.now(),
            amount=Decimal("200.00"),
            currency="EUR",
            payment_method="debit_card",
            payment_status="pending",
            customer_id="cust-456",
            metadata={"key": "value"}
        )
        assert tx.customer_id == "cust-456"
        assert tx.metadata == {"key": "value"}


class TestNormalizedTransaction:
    """Tests for NormalizedTransaction model."""
    
    def test_valid_normalized_transaction(self, sample_normalized_transaction):
        """Test creating a valid normalized transaction."""
        assert sample_normalized_transaction.transaction_id == "tx-123"
        assert sample_normalized_transaction.amount > 0
    
    def test_invalid_amount_negative(self):
        """Test that negative amounts are rejected."""
        with pytest.raises(ValidationError):
            NormalizedTransaction(
                transaction_id="tx-123",
                transaction_timestamp=datetime.now(),
                amount=Decimal("-100.00"),
                currency="USD",
                payment_method="credit_card",
                payment_status="completed"
            )
    
    def test_invalid_currency_length(self):
        """Test that invalid currency codes are rejected."""
        with pytest.raises(ValidationError):
            NormalizedTransaction(
                transaction_id="tx-123",
                transaction_timestamp=datetime.now(),
                amount=Decimal("100.00"),
                currency="US",  # Too short
                payment_method="credit_card",
                payment_status="completed"
            )
    
    def test_invalid_payment_status(self):
        """Test that invalid payment status is rejected."""
        with pytest.raises(ValidationError):
            NormalizedTransaction(
                transaction_id="tx-123",
                transaction_timestamp=datetime.now(),
                amount=Decimal("100.00"),
                currency="USD",
                payment_method="credit_card",
                payment_status="invalid_status"
            )
    
    def test_country_code_normalization(self):
        """Test country code length validation."""
        tx = NormalizedTransaction(
            transaction_id="tx-123",
            transaction_timestamp=datetime.now(),
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
            customer_country="US"
        )
        assert tx.customer_country == "US"


class TestDerivedMetric:
    """Tests for DerivedMetric model."""
    
    def test_valid_derived_metric(self):
        """Test creating a valid derived metric."""
        metric = DerivedMetric(
            transaction_id="tx-123",
            metric_name="high_value_count",
            metric_value=Decimal("1"),
            metric_type="count",
            rule_name="high_value_rule",
            rule_version="1.0.0"
        )
        assert metric.metric_name == "high_value_count"
        assert metric.metric_type == "count"
    
    def test_invalid_metric_type(self):
        """Test that invalid metric type is rejected."""
        with pytest.raises(ValidationError):
            DerivedMetric(
                transaction_id="tx-123",
                metric_name="test_metric",
                metric_value=Decimal("1"),
                metric_type="invalid_type",
                rule_name="test_rule",
                rule_version="1.0.0"
            )


class TestAggregatedMetric:
    """Tests for AggregatedMetric model."""
    
    def test_valid_aggregated_metric(self, sample_aggregated_metric):
        """Test creating a valid aggregated metric."""
        assert sample_aggregated_metric.total_count == 10
        assert sample_aggregated_metric.total_amount == Decimal("1000.00")
        assert sample_aggregated_metric.avg_amount == Decimal("100.00")


class TestCluster:
    """Tests for Cluster model."""
    
    def test_valid_cluster(self, sample_cluster):
        """Test creating a valid cluster."""
        assert sample_cluster.cluster_id == 1
        assert len(sample_cluster.transaction_ids) == 3
        assert sample_cluster.size == 3
        assert sample_cluster.algorithm == "kmeans"


class TestTimeWindow:
    """Tests for TimeWindow model."""
    
    def test_valid_time_window(self, sample_time_window):
        """Test creating a valid time window."""
        assert sample_time_window.name == "hourly"
        assert sample_time_window.duration_seconds == 3600
        assert sample_time_window.enabled is True
    
    def test_time_window_contains(self, sample_time_window):
        """Test time window contains method."""
        from datetime import timedelta
        
        # Timestamp within window
        within = sample_time_window.start_time + timedelta(minutes=30)
        assert sample_time_window.contains(within) is True
        
        # Timestamp before window
        before = sample_time_window.start_time - timedelta(minutes=1)
        assert sample_time_window.contains(before) is False
        
        # Timestamp at end (exclusive)
        at_end = sample_time_window.end_time
        assert sample_time_window.contains(at_end) is False

