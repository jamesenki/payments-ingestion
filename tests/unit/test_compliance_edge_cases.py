"""
Edge case tests for ComplianceViolationGenerator to increase coverage.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch

from simulator.compliance_generator import ComplianceViolationGenerator
from simulator.models import Transaction
from simulator.config.schema import ComplianceConfig, ComplianceScenario


class TestComplianceEdgeCases:
    """Edge case tests for ComplianceViolationGenerator."""
    
    def test_apply_aml_violation_no_patterns(self):
        """Test AML violation with no enabled patterns."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={}  # No patterns
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"aml_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            # Should return unknown violation
            assert "aml_unknown" in violations or len(violations) == 0
    
    def test_apply_kyc_violation_no_patterns(self):
        """Test KYC violation with no enabled patterns."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={}
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"kyc_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            assert "kyc_unknown" in violations or len(violations) == 0
    
    def test_apply_pci_violation_no_patterns(self):
        """Test PCI violation with no enabled patterns."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={}
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"pci_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            assert "pci_unknown" in violations or len(violations) == 0
    
    def test_apply_business_rule_no_patterns(self):
        """Test business rule violation with no enabled patterns."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={}
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"business_rule_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            assert "business_rule_unknown" in violations or len(violations) == 0
    
    def test_apply_aml_structuring_with_threshold(self):
        """Test AML structuring with custom threshold."""
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
                "structuring": {
                    "enabled": True,
                    "frequency": 1.0,
                    "threshold": 5000.0,
                }
            }
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"aml_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            assert "aml_structuring" in violations
            assert float(tx.amount) < 5000.0

