"""
Integration tests for the full simulator flow.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from simulator.main import SimulatorApp
from simulator.config.loader import load_config


class MockPublisher:
    """Mock publisher for testing."""
    
    def __init__(self, config):
        self.config = config
        self.published = []
        self.batch = []
    
    async def publish_batch(self, transactions):
        """Mock publish batch."""
        self.published.extend(transactions)
        return len(transactions)
    
    async def flush_batch(self):
        """Mock flush batch."""
        return len(self.batch)
    
    async def close(self):
        """Mock close."""
        pass
    
    def get_metrics(self):
        """Mock get metrics."""
        return {
            "total_published": len(self.published),
            "total_failed": 0,
        }


async def test_full_simulation_flow():
    """Test the full simulation flow with mock publisher."""
    print("\n🧪 Testing Full Simulation Flow...")
    
    # Create app
    config_path = Path(__file__).parent.parent / "config" / "simulator_config.yaml"
    if not config_path.exists():
        pytest.skip(f"Config file not found: {config_path}")
    
    # Set dummy env var to avoid error
    import os
    os.environ["EVENTHUB_CONNECTION_STRING"] = "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test;EntityPath=test"
    
    # Mock the publisher
    mock_publisher = MockPublisher({})
    
    with patch('simulator.main.create_publisher') as mock_create:
        mock_create.return_value = mock_publisher
        
        app = SimulatorApp(config_path=str(config_path))
        
        # Initialize
        app.initialize()
        
        # Verify publisher was created
        assert app.publisher is not None
        print("   ✅ Publisher initialized")
        
        # Verify transaction generator
        assert app.transaction_generator is not None
        print("   ✅ Transaction generator initialized")
        
        # Verify compliance generator
        assert app.compliance_generator is not None
        print("   ✅ Compliance generator initialized")
        
        # Run a small simulation (10 transactions)
        # Temporarily modify config for small test
        app.config.simulator["transaction"]["volume"]["total"] = 10
        app.config.simulator["transaction"]["volume"]["rate"] = 10
        
        # Run simulation
        await app.run()
        
        # Verify transactions were published
        assert len(mock_publisher.published) > 0
        print(f"   ✅ Published {len(mock_publisher.published)} transactions")
        
        # Verify transaction structure
        tx = mock_publisher.published[0]
        assert "transaction_id" in tx
        assert "amount" in tx
        assert "currency" in tx
        assert "payment_method" in tx
        print("   ✅ Transaction structure valid")
        
        # Check for compliance violations
        violations_count = sum(
            1 for tx in mock_publisher.published
            if tx.get("compliance_violations")
        )
        print(f"   ✅ Found {violations_count} transactions with violations")
        
        print("   ✅ Full simulation flow: PASSED")


def test_configuration_validation():
    """Test configuration validation."""
    print("\n🧪 Testing Configuration Validation...")
    
    config_path = Path(__file__).parent.parent / "config" / "simulator_config.yaml"
    if not config_path.exists():
        pytest.skip(f"Config file not found: {config_path}")
    
    config = load_config(str(config_path), enable_reload=False)
    
    # Validate structure
    assert config.simulator is not None
    assert "output" in config.simulator
    assert "transaction" in config.simulator
    
    # Validate output config
    output = config.simulator["output"]
    assert output["destination"] == "event_hub"
    assert output["batch_size"] > 0
    
    # Validate transaction config
    transaction = config.simulator["transaction"]
    assert "volume" in transaction
    assert "variability" in transaction
    
    # Validate compliance config
    assert config.compliance is not None
    assert config.compliance.enabled is True
    
    print("   ✅ Configuration validation: PASSED")


def test_variability_distributions():
    """Test that variability distributions work correctly."""
    print("\n🧪 Testing Variability Distributions...")
    
    from simulator.transaction_generator import TransactionGenerator
    from simulator.config.schema import TransactionConfig, VariabilityConfig
    
    # Create config with specific distributions
    config = TransactionConfig(
        volume={"total": 100, "rate": 100},
        variability=VariabilityConfig(
            payment_methods={
                "credit_card": 1.0  # 100% credit card for testing
            },
            currencies={
                "USD": 1.0  # 100% USD for testing
            }
        )
    )
    
    generator = TransactionGenerator(config)
    
    # Generate transactions
    transactions = generator.generate_batch(50)
    
    # Verify all are credit card
    credit_card_count = sum(1 for tx in transactions if tx.payment_method == "credit_card")
    assert credit_card_count == 50
    
    # Verify all are USD
    usd_count = sum(1 for tx in transactions if tx.currency == "USD")
    assert usd_count == 50
    
    print("   ✅ Variability distributions: PASSED")


if __name__ == "__main__":
    print("=" * 60)
    print("SIMULATOR INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        test_configuration_validation()
        test_variability_distributions()
        asyncio.run(test_full_simulation_flow())
        
        print()
        print("=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

