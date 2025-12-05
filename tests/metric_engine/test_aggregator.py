"""
Unit tests for aggregator.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.metric_engine.aggregator import Aggregator
from src.metric_engine.models import NormalizedTransaction, TimeWindow


class TestAggregator:
    """Tests for Aggregator."""
    
    @pytest.fixture
    def sample_time_window(self):
        """Create a sample time window."""
        start = datetime.now().replace(minute=0, second=0, microsecond=0)
        return TimeWindow(
            name="hourly",
            duration_seconds=3600,
            start_time=start,
            end_time=start + timedelta(hours=1),
            enabled=True
        )
    
    @pytest.fixture
    def sample_transactions(self, sample_time_window):
        """Create sample transactions within time window."""
        transactions = []
        base_time = sample_time_window.start_time
        
        for i in range(5):
            transactions.append(
                NormalizedTransaction(
                    transaction_id=f"tx-{i}",
                    transaction_timestamp=base_time + timedelta(minutes=i * 10),
                    amount=Decimal(f"{100 + i * 10}.00"),
                    currency="USD",
                    payment_method="credit_card" if i % 2 == 0 else "debit_card",
                    payment_status="completed" if i < 4 else "failed",
                    customer_id=f"cust-{i % 2}",
                    merchant_id=f"merch-{i % 2}"
                )
            )
        
        return transactions
    
    def test_aggregate_single_group(self, sample_time_window, sample_transactions):
        """Test aggregating transactions in a single group."""
        aggregator = Aggregator(
            dimensions=["currency"],
            operations=["sum", "average", "count"],
            time_window=sample_time_window
        )
        
        metrics = aggregator.aggregate(sample_transactions)
        
        assert len(metrics) == 1
        metric = metrics[0]
        assert metric.total_count == 5
        assert metric.total_amount == Decimal("600.00")  # 100+110+120+130+140
        assert metric.avg_amount == Decimal("120.00")
    
    def test_aggregate_multiple_groups(self, sample_time_window, sample_transactions):
        """Test aggregating transactions into multiple groups."""
        aggregator = Aggregator(
            dimensions=["payment_method"],
            operations=["sum", "count"],
            time_window=sample_time_window
        )
        
        metrics = aggregator.aggregate(sample_transactions)
        
        # Should have 2 groups: credit_card and debit_card
        assert len(metrics) == 2
        
        credit_card_metric = next(
            (m for m in metrics if m.dimensions["payment_method"] == "credit_card"),
            None
        )
        assert credit_card_metric is not None
        assert credit_card_metric.total_count == 3  # tx-0, tx-2, tx-4
    
    def test_aggregate_with_status_breakdown(self, sample_time_window, sample_transactions):
        """Test aggregation includes status breakdown."""
        aggregator = Aggregator(
            dimensions=["currency"],
            operations=["sum", "count"],
            time_window=sample_time_window
        )
        
        metrics = aggregator.aggregate(sample_transactions)
        
        assert len(metrics) == 1
        metric = metrics[0]
        assert "status_breakdown" in metric.additional_metrics
        assert metric.additional_metrics["status_breakdown"]["completed"] == 4
        assert metric.additional_metrics["status_breakdown"]["failed"] == 1
    
    def test_aggregate_with_payment_method_breakdown(self, sample_time_window, sample_transactions):
        """Test aggregation includes payment method breakdown."""
        aggregator = Aggregator(
            dimensions=["currency"],
            operations=["sum", "count"],
            time_window=sample_time_window
        )
        
        metrics = aggregator.aggregate(sample_transactions)
        
        assert len(metrics) == 1
        metric = metrics[0]
        assert "payment_method_breakdown" in metric.additional_metrics
        breakdown = metric.additional_metrics["payment_method_breakdown"]
        assert breakdown["credit_card"] == 3
        assert breakdown["debit_card"] == 2
    
    def test_aggregate_unique_customers(self, sample_time_window, sample_transactions):
        """Test aggregation counts unique customers."""
        aggregator = Aggregator(
            dimensions=["currency"],
            operations=["sum", "count"],
            time_window=sample_time_window
        )
        
        metrics = aggregator.aggregate(sample_transactions)
        
        assert len(metrics) == 1
        metric = metrics[0]
        assert "unique_customers" in metric.additional_metrics
        # Should have 2 unique customers (cust-0 and cust-1)
        assert metric.additional_metrics["unique_customers"] == 2
    
    def test_aggregate_unique_merchants(self, sample_time_window, sample_transactions):
        """Test aggregation counts unique merchants."""
        aggregator = Aggregator(
            dimensions=["currency"],
            operations=["sum", "count"],
            time_window=sample_time_window
        )
        
        metrics = aggregator.aggregate(sample_transactions)
        
        assert len(metrics) == 1
        metric = metrics[0]
        assert "unique_merchants" in metric.additional_metrics
        # Should have 2 unique merchants
        assert metric.additional_metrics["unique_merchants"] == 2
    
    def test_aggregate_min_max(self, sample_time_window, sample_transactions):
        """Test aggregation calculates min and max amounts."""
        aggregator = Aggregator(
            dimensions=["currency"],
            operations=["sum", "count", "min", "max"],
            time_window=sample_time_window
        )
        
        metrics = aggregator.aggregate(sample_transactions)
        
        assert len(metrics) == 1
        metric = metrics[0]
        assert metric.min_amount == Decimal("100.00")
        assert metric.max_amount == Decimal("140.00")
    
    def test_aggregate_outside_window(self, sample_time_window):
        """Test that transactions outside window are excluded."""
        # Create transaction outside window
        outside_tx = NormalizedTransaction(
            transaction_id="tx-outside",
            transaction_timestamp=sample_time_window.start_time - timedelta(hours=1),
            amount=Decimal("1000.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed"
        )
        
        aggregator = Aggregator(
            dimensions=["currency"],
            operations=["count"],
            time_window=sample_time_window
        )
        
        metrics = aggregator.aggregate([outside_tx])
        
        # Should have no metrics (transaction outside window)
        assert len(metrics) == 0
    
    def test_aggregate_empty_list(self, sample_time_window):
        """Test aggregating empty transaction list."""
        aggregator = Aggregator(
            dimensions=["currency"],
            operations=["count"],
            time_window=sample_time_window
        )
        
        metrics = aggregator.aggregate([])
        
        assert len(metrics) == 0
    
    def test_aggregate_multiple_dimensions(self, sample_time_window, sample_transactions):
        """Test aggregation with multiple dimensions."""
        aggregator = Aggregator(
            dimensions=["payment_method", "currency"],
            operations=["sum", "count"],
            time_window=sample_time_window
        )
        
        metrics = aggregator.aggregate(sample_transactions)
        
        # Should have 2 groups: (credit_card, USD) and (debit_card, USD)
        assert len(metrics) == 2
        
        for metric in metrics:
            assert "payment_method" in metric.dimensions
            assert "currency" in metric.dimensions

