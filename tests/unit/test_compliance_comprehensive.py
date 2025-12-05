"""
Comprehensive unit tests for ComplianceViolationGenerator to increase coverage.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch

from simulator.compliance_generator import ComplianceViolationGenerator
from simulator.models import Transaction
from simulator.config.schema import ComplianceConfig, ComplianceScenario


class TestComplianceGeneratorComprehensive:
    """Comprehensive tests for ComplianceViolationGenerator."""
    
    def test_apply_pci_violation_missing_card_data(self):
        """Test PCI missing card data violation."""
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
                "missing_card_data": {
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
            
            assert "pci_missing_card_data" in violations
    
    def test_apply_business_rule_orphan_refund(self):
        """Test business rule orphan refund violation."""
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
                "orphan_refund": {
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
            
            assert "business_rule_orphan_refund" in violations
            assert tx.payment_status == "refunded"
    
    def test_apply_business_rule_currency_mismatch(self):
        """Test business rule currency mismatch violation."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
            customer_country="US",
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
            
            assert "business_rule_currency_mismatch" in violations
            assert tx.currency == "EUR"  # Changed from USD
    
    def test_determine_severity_critical(self):
        """Test severity determination for critical violations."""
        config = ComplianceConfig(enabled=True)
        generator = ComplianceViolationGenerator(config)
        
        severity = generator._determine_severity(["aml_large_amount"])
        assert severity == "critical"
        
        severity = generator._determine_severity(["pci_missing_card_data"])
        assert severity == "critical"
    
    def test_determine_severity_high(self):
        """Test severity determination for high violations."""
        config = ComplianceConfig(enabled=True)
        generator = ComplianceViolationGenerator(config)
        
        severity = generator._determine_severity(["aml_structuring"])
        assert severity == "high"
        
        severity = generator._determine_severity(["kyc_missing_customer_id"])
        assert severity == "high"
    
    def test_determine_severity_medium(self):
        """Test severity determination for medium violations."""
        config = ComplianceConfig(enabled=True)
        generator = ComplianceViolationGenerator(config)
        
        severity = generator._determine_severity(["data_quality_negative_amount"])
        assert severity == "medium"
        
        severity = generator._determine_severity(["data_quality_zero_amount"])
        assert severity == "medium"
    
    def test_determine_severity_low(self):
        """Test severity determination for low violations."""
        config = ComplianceConfig(enabled=True)
        generator = ComplianceViolationGenerator(config)
        
        severity = generator._determine_severity(["unknown_violation"])
        assert severity == "low"
    
    def test_apply_violation_with_custom_scenarios(self):
        """Test applying violation with custom scenarios."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        custom_scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "structuring": {
                    "enabled": True,
                    "frequency": 1.0,
                    "threshold": 5000.0,
                }
            }
        )
        
        config = ComplianceConfig(enabled=True, total_violation_percentage=1.0)
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(
                transaction,
                scenarios={"aml_violations": custom_scenario}
            )
            
            # Should have applied violation
            assert len(violations) > 0 or tx.compliance_violations

