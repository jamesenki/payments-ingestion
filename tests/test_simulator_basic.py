"""
Basic functional tests for the simulator components.
"""

import pytest
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from simulator.config.loader import load_config
from simulator.transaction_generator import TransactionGenerator
from simulator.compliance_generator import ComplianceViolationGenerator
from simulator.models import Transaction
from simulator.config.schema import TransactionConfig, ComplianceConfig


def test_config_loading():
    """Test that configuration can be loaded."""
    config_path = Path(__file__).parent.parent / "config" / "simulator_config.yaml"
    
    if not config_path.exists():
        pytest.skip(f"Config file not found: {config_path}")
    
    config = load_config(str(config_path), enable_reload=False)
    assert config is not None
    assert config.simulator is not None
    print("✅ Configuration loading: PASSED")


def test_transaction_generation():
    """Test transaction generation."""
    # Create minimal config
    transaction_config = TransactionConfig(
        volume={"total": 10, "rate": 10},
        variability={}
    )
    
    generator = TransactionGenerator(transaction_config)
    
    # Generate a single transaction
    transaction = generator.generate_transaction()
    
    assert transaction is not None
    assert transaction.transaction_id is not None
    assert transaction.amount > 0
    assert len(transaction.currency) == 3
    assert transaction.payment_method is not None
    assert transaction.payment_status is not None
    
    print("✅ Transaction generation: PASSED")
    print(f"   Generated: {transaction.transaction_id}, Amount: {transaction.amount} {transaction.currency}")


def test_transaction_batch_generation():
    """Test batch transaction generation."""
    transaction_config = TransactionConfig(
        volume={"total": 10, "rate": 10},
        variability={}
    )
    
    generator = TransactionGenerator(transaction_config)
    
    # Generate batch
    transactions = generator.generate_batch(5)
    
    assert len(transactions) == 5
    assert all(isinstance(t, Transaction) for t in transactions)
    
    print("✅ Batch generation: PASSED")
    print(f"   Generated {len(transactions)} transactions")


def test_compliance_violations():
    """Test compliance violation generation."""
    compliance_config = ComplianceConfig(
        enabled=True,
        total_violation_percentage=1.0,  # 100% for testing
        scenarios={
            "data_quality_violations": {
                "enabled": True,
                "percentage": 1.0,
                "patterns": {
                    "negative_amount": {
                        "enabled": True,
                        "frequency": 1.0
                    }
                }
            }
        }
    )
    
    generator = ComplianceViolationGenerator(compliance_config)
    
    # Create a test transaction
    transaction_config = TransactionConfig(
        volume={"total": 1, "rate": 1},
        variability={}
    )
    tx_gen = TransactionGenerator(transaction_config)
    transaction = tx_gen.generate_transaction()
    
    # Apply violation
    modified_tx, violations = generator.apply_violation(transaction)
    
    assert violations is not None
    assert len(violations) > 0 or modified_tx.compliance_violations
    
    print("✅ Compliance violation generation: PASSED")
    print(f"   Violations: {violations}")


def test_transaction_serialization():
    """Test transaction serialization to dict."""
    transaction_config = TransactionConfig(
        volume={"total": 1, "rate": 1},
        variability={}
    )
    
    generator = TransactionGenerator(transaction_config)
    transaction = generator.generate_transaction()
    
    # Test serialization
    tx_dict = transaction.to_dict()
    assert isinstance(tx_dict, dict)
    assert "transaction_id" in tx_dict
    assert "amount" in tx_dict
    assert "currency" in tx_dict
    
    # Test Event Hub format
    event_hub_dict = transaction.to_event_hub_format()
    assert isinstance(event_hub_dict, dict)
    
    print("✅ Transaction serialization: PASSED")


def test_amount_distributions():
    """Test different amount distributions."""
    transaction_config = TransactionConfig(
        volume={"total": 100, "rate": 100},
        variability={
            "amounts": {
                "distribution": "normal",
                "mean": 100.0,
                "std_dev": 50.0,
                "min": 1.0,
                "max": 1000.0
            }
        }
    )
    
    generator = TransactionGenerator(transaction_config)
    
    amounts = []
    for _ in range(100):
        tx = generator.generate_transaction()
        amounts.append(float(tx.amount))
    
    # Verify amounts are in range
    assert all(1.0 <= amt <= 1000.0 for amt in amounts)
    assert len(amounts) == 100
    
    print("✅ Amount distributions: PASSED")
    print(f"   Min: {min(amounts):.2f}, Max: {max(amounts):.2f}, Avg: {sum(amounts)/len(amounts):.2f}")


if __name__ == "__main__":
    print("=" * 60)
    print("SIMULATOR BASIC FUNCTIONAL TESTS")
    print("=" * 60)
    print()
    
    try:
        test_config_loading()
        test_transaction_generation()
        test_transaction_batch_generation()
        test_compliance_violations()
        test_transaction_serialization()
        test_amount_distributions()
        
        print()
        print("=" * 60)
        print("✅ ALL BASIC TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

