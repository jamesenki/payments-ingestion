"""
Pytest fixtures for metric engine tests.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import MagicMock, Mock

# Import with src prefix
from src.metric_engine.models import (
    RawTransaction,
    NormalizedTransaction,
    DerivedMetric,
    AggregatedMetric,
    Cluster,
    TimeWindow
)


@pytest.fixture
def sample_raw_transaction() -> RawTransaction:
    """Create a sample raw transaction."""
    return RawTransaction(
        transaction_id="tx-123",
        transaction_timestamp=datetime.now(),
        amount=Decimal("100.50"),
        currency="USD",
        payment_method="credit_card",
        payment_status="completed",
        customer_id="cust-123",
        customer_email="test@example.com",
        customer_country="US",
        merchant_id="merch-123",
        merchant_name="Test Merchant",
        merchant_category="retail"
    )


@pytest.fixture
def sample_normalized_transaction() -> NormalizedTransaction:
    """Create a sample normalized transaction."""
    return NormalizedTransaction(
        transaction_id="tx-123",
        transaction_timestamp=datetime.now(),
        amount=Decimal("100.50"),
        currency="USD",
        payment_method="credit_card",
        payment_status="completed",
        customer_id="cust-123",
        customer_email="test@example.com",
        customer_country="US",
        merchant_id="merch-123",
        merchant_name="Test Merchant",
        merchant_category="retail"
    )


@pytest.fixture
def sample_transactions() -> list[NormalizedTransaction]:
    """Create multiple sample transactions."""
    base_time = datetime.now()
    transactions = []
    
    for i in range(10):
        transactions.append(
            NormalizedTransaction(
                transaction_id=f"tx-{i}",
                transaction_timestamp=base_time + timedelta(minutes=i),
                amount=Decimal(f"{50 + i * 10}.00"),
                currency="USD",
                payment_method="credit_card" if i % 2 == 0 else "debit_card",
                payment_status="completed" if i < 8 else "failed",
                customer_id=f"cust-{i % 3}",
                customer_country="US",
                merchant_id=f"merch-{i % 2}"
            )
        )
    
    return transactions


@pytest.fixture
def sample_time_window() -> TimeWindow:
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
def sample_5min_window() -> TimeWindow:
    """Create a 5-minute time window."""
    start = datetime.now().replace(minute=0, second=0, microsecond=0)
    return TimeWindow(
        name="5min",
        duration_seconds=300,
        start_time=start,
        end_time=start + timedelta(minutes=5),
        enabled=True
    )


@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
    return mock_conn, mock_cursor


@pytest.fixture
def sample_rule_config() -> Dict[str, Any]:
    """Sample rule configuration."""
    return {
        "name": "high_value_transaction_count",
        "description": "Count transactions above threshold",
        "enabled": True,
        "metric_name": "high_value_count",
        "metric_type": "count",
        "metric_category": "transaction_volume",
        "condition": {
            "field": "amount",
            "operator": ">",
            "value": 1000.00
        },
        "rule_version": "1.0.0"
    }


@pytest.fixture
def sample_aggregated_metric() -> AggregatedMetric:
    """Create a sample aggregated metric."""
    start = datetime.now().replace(minute=0, second=0, microsecond=0)
    return AggregatedMetric(
        window_start=start,
        window_end=start + timedelta(hours=1),
        dimensions={"payment_method": "credit_card", "currency": "USD"},
        total_count=10,
        total_amount=Decimal("1000.00"),
        avg_amount=Decimal("100.00"),
        min_amount=Decimal("50.00"),
        max_amount=Decimal("150.00")
    )


@pytest.fixture
def sample_cluster() -> Cluster:
    """Create a sample cluster."""
    start = datetime.now().replace(minute=0, second=0, microsecond=0)
    return Cluster(
        cluster_id=1,
        transaction_ids=["tx-1", "tx-2", "tx-3"],
        centroid={"amount": 100.0, "payment_method_encoded": 1.0},
        size=3,
        time_window_start=start,
        time_window_end=start + timedelta(hours=1),
        algorithm="kmeans",
        similarity_metric="euclidean"
    )

