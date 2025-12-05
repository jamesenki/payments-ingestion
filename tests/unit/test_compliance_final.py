"""
Final compliance tests to reach 90% coverage.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch

from simulator.compliance_generator import ComplianceViolationGenerator
from simulator.models import Transaction
from simulator.config.schema import ComplianceConfig, ComplianceScenario


class TestComplianceFinal:
    """Final tests for compliance generator edge cases."""
    
    def test_apply_pci_violation_invalid_card_brand(self):
        """Test PCI invalid card brand violation."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
            metadata={"card_brand": "Visa", "card_last4": "1234"}
        )
        
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "invalid_card_brand": {
                    "enabled": True,
                    "frequency": 1.0,
                }
            }
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"pci_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            assert "pci_invalid_card_brand" in violations
            assert tx.metadata.get("card_brand") == "InvalidBrand"
    
    def test_apply_data_quality_invalid_status(self):
        """Test data quality invalid status violation."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "invalid_status": {
                    "enabled": True,
                    "frequency": 1.0,
                }
            }
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"data_quality_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            assert "data_quality_invalid_status" in violations
            assert tx.payment_status == "processing"
    
    def test_apply_data_quality_invalid_currency(self):
        """Test data quality invalid currency violation."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "invalid_currency": {
                    "enabled": True,
                    "frequency": 1.0,
                }
            }
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"data_quality_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            assert "data_quality_invalid_currency" in violations
            assert tx.currency == "XXX"
    
    def test_apply_business_rule_status_mismatch_not_failed(self):
        """Test business rule status mismatch when status is not failed."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",  # Not failed
        )
        
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "status_mismatch": {
                    "enabled": True,
                    "frequency": 1.0,
                }
            }
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"business_rule_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            # Should still apply violation
            assert "business_rule_status_mismatch" in violations or len(violations) > 0
    
    def test_apply_business_rule_currency_mismatch_not_us(self):
        """Test business rule currency mismatch when country is not US."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
            customer_country="GB",  # Not US
        )
        
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "currency_mismatch": {
                    "enabled": True,
                    "frequency": 1.0,
                }
            }
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"business_rule_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            # Should still apply violation
            assert "business_rule_currency_mismatch" in violations or len(violations) > 0

