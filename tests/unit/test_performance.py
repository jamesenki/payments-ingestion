"""
Performance tests for simulator components.
"""

import pytest
import time
from decimal import Decimal

from simulator.transaction_generator import TransactionGenerator
from simulator.compliance_generator import ComplianceViolationGenerator
from simulator.config.schema import TransactionConfig, VariabilityConfig, ComplianceConfig
from conftest import minimal_transaction_config, compliance_config


class TestPerformance:
    """Performance tests."""
    
    def test_transaction_generation_throughput(self, minimal_transaction_config):
        """Test transaction generation throughput."""
        generator = TransactionGenerator(minimal_transaction_config)
        
        start = time.time()
        transactions = generator.generate_batch(1000)
        elapsed = time.time() - start
        
        assert len(transactions) == 1000
        assert elapsed < 5.0  # Should generate 1000 transactions in < 5 seconds
        
        throughput = len(transactions) / elapsed
        print(f"Transaction generation throughput: {throughput:.0f} tx/s")
        assert throughput > 100  # At least 100 transactions per second
    
    def test_compliance_violation_throughput(self, sample_transaction, compliance_config):
        """Test compliance violation application throughput."""
        generator = ComplianceViolationGenerator(compliance_config)
        
        start = time.time()
        for _ in range(1000):
            generator.apply_violation(sample_transaction)
        elapsed = time.time() - start
        
        assert elapsed < 5.0  # Should process 1000 violations in < 5 seconds
        
        throughput = 1000 / elapsed
        print(f"Compliance violation throughput: {throughput:.0f} violations/s")
        assert throughput > 100  # At least 100 violations per second
    
    def test_amount_generation_performance(self, minimal_transaction_config):
        """Test amount generation performance."""
        config = TransactionConfig(
            volume={"total": 100, "rate": 10},
            variability=VariabilityConfig(
                amounts={
                    "distribution": "normal",
                    "mean": 100.0,
                    "std_dev": 50.0,
                    "min": 1.0,
                    "max": 1000.0,
                }
            )
        )
        generator = TransactionGenerator(config)
        
        start = time.time()
        amounts = [generator.generate_amount() for _ in range(10000)]
        elapsed = time.time() - start
        
        assert len(amounts) == 10000
        assert elapsed < 1.0  # Should generate 10000 amounts in < 1 second
        
        throughput = 10000 / elapsed
        print(f"Amount generation throughput: {throughput:.0f} amounts/s")
        assert throughput > 5000  # At least 5000 amounts per second
    
    def test_batch_serialization_performance(self, minimal_transaction_config):
        """Test batch serialization performance."""
        generator = TransactionGenerator(minimal_transaction_config)
        transactions = generator.generate_batch(1000)
        
        start = time.time()
        dicts = [tx.to_dict() for tx in transactions]
        elapsed = time.time() - start
        
        assert len(dicts) == 1000
        assert elapsed < 1.0  # Should serialize 1000 transactions in < 1 second
        
        throughput = 1000 / elapsed
        print(f"Serialization throughput: {throughput:.0f} tx/s")
        assert throughput > 500  # At least 500 serializations per second

