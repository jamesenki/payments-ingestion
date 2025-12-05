"""
Pytest fixtures and test utilities.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import tempfile
import yaml
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any

from simulator.models import Transaction
from simulator.config.schema import (
    TransactionConfig,
    VariabilityConfig,
    ComplianceConfig,
    ComplianceScenario,
    SimulatorConfig,
    OutputConfig,
    MetadataConfig,
    LoggingConfig,
)


@pytest.fixture
def sample_transaction() -> Transaction:
    """Create a sample transaction for testing."""
    return Transaction(
        transaction_id="test-123",
        amount=Decimal("100.50"),
        currency="USD",
        payment_method="credit_card",
        payment_status="completed",
        customer_id="cust-123",
        customer_email="test@example.com",
        customer_country="US",
        merchant_id="merch-123",
        merchant_name="Test Merchant",
        merchant_category="retail",
    )


@pytest.fixture
def sample_transaction_dict() -> Dict[str, Any]:
    """Create a sample transaction dictionary."""
    return {
        "transaction_id": "test-123",
        "amount": 100.50,
        "currency": "USD",
        "payment_method": "credit_card",
        "payment_status": "completed",
        "customer_id": "cust-123",
        "customer_email": "test@example.com",
        "customer_country": "US",
        "merchant_id": "merch-123",
        "merchant_name": "Test Merchant",
        "merchant_category": "retail",
    }


@pytest.fixture
def minimal_transaction_config() -> TransactionConfig:
    """Create minimal transaction config for testing."""
    return TransactionConfig(
        volume={"total": 100, "rate": 10},
        variability=VariabilityConfig()
    )


@pytest.fixture
def full_transaction_config() -> TransactionConfig:
    """Create full transaction config for testing."""
    return TransactionConfig(
        volume={"total": 1000, "rate": 100},
        variability=VariabilityConfig(
            amounts={
                "distribution": "normal",
                "mean": 100.0,
                "std_dev": 50.0,
                "min": 1.0,
                "max": 1000.0,
            },
            payment_methods={
                "credit_card": 0.6,
                "debit_card": 0.3,
                "paypal": 0.1,
            },
            currencies={
                "USD": 0.7,
                "EUR": 0.2,
                "GBP": 0.1,
            },
        )
    )


@pytest.fixture
def compliance_config() -> ComplianceConfig:
    """Create compliance config for testing."""
    return ComplianceConfig(
        enabled=True,
        total_violation_percentage=0.1,
        scenarios={
            "aml_violations": ComplianceScenario(
                enabled=True,
                percentage=0.05,
                patterns={
                    "structuring": {
                        "enabled": True,
                        "frequency": 0.5,
                    }
                }
            ),
            "data_quality_violations": ComplianceScenario(
                enabled=True,
                percentage=0.05,
                patterns={
                    "negative_amount": {
                        "enabled": True,
                        "frequency": 1.0,
                    }
                }
            )
        }
    )


@pytest.fixture
def sample_config_file(tmp_path) -> Path:
    """Create a sample config file for testing."""
    config_data = {
        "simulator": {
            "output": {
                "destination": "event_hub",
                "batch_size": 100,
            },
            "transaction": {
                "volume": {
                    "total": 1000,
                    "rate": 100,
                },
                "variability": {},
            },
        },
        "compliance": {
            "enabled": True,
            "total_violation_percentage": 0.1,
            "scenarios": {},
        },
    }
    
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    
    return config_file


@pytest.fixture
def mock_event_hub_connection_string(monkeypatch):
    """Set mock Event Hub connection string."""
    monkeypatch.setenv(
        "EVENTHUB_CONNECTION_STRING",
        "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test;EntityPath=test"
    )


@pytest.fixture
def mock_publisher():
    """Create a mock publisher for testing."""
    class MockPublisher:
        def __init__(self, config):
            self.config = config
            self.published = []
            self.batch = []
        
        async def publish(self, transaction):
            self.published.append(transaction)
            return True
        
        async def publish_batch(self, transactions):
            self.published.extend(transactions)
            return len(transactions)
        
        async def flush_batch(self):
            return len(self.batch)
        
        async def close(self):
            pass
        
        def get_metrics(self):
            return {
                "total_published": len(self.published),
                "total_failed": 0,
            }
    
    return MockPublisher

