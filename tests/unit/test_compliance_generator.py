"""
Unit tests for ComplianceViolationGenerator.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch

from simulator.compliance_generator import ComplianceViolationGenerator
from simulator.models import Transaction
from simulator.config.schema import ComplianceConfig, ComplianceScenario
from conftest import compliance_config, sample_transaction


class TestComplianceViolationGenerator:
    """Test ComplianceViolationGenerator class."""
    
    def test_initialization(self, compliance_config):
        """Test generator initialization."""
        generator = ComplianceViolationGenerator(compliance_config)
        
        assert generator.config == compliance_config
        assert generator.violation_history == []
    
    def test_should_apply_violation_enabled(self, compliance_config):
        """Test violation application when enabled."""
        generator = ComplianceViolationGenerator(compliance_config)
        
        # With 100% violation percentage, should always apply
        compliance_config.total_violation_percentage = 1.0
        assert generator.should_apply_violation() is True
    
    def test_should_apply_violation_disabled(self):
        """Test violation application when disabled."""
        config = ComplianceConfig(enabled=False)
        generator = ComplianceViolationGenerator(config)
        
        assert generator.should_apply_violation() is False
    
    def test_apply_violation_when_disabled(self, sample_transaction):
        """Test applying violation when disabled."""
        config = ComplianceConfig(enabled=False)
        generator = ComplianceViolationGenerator(config)
        
        tx, violations = generator.apply_violation(sample_transaction)
        
        assert tx == sample_transaction
        assert violations == []
    
    def test_apply_aml_violation_structuring(self, sample_transaction, compliance_config):
        """Test AML structuring violation."""
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "structuring": {
                    "enabled": True,
                    "frequency": 1.0,
                    "threshold": 10000.0,
                }
            }
        )
        compliance_config.scenarios = {"aml_violations": scenario}
        generator = ComplianceViolationGenerator(compliance_config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(sample_transaction)
            
            assert "aml_structuring" in violations
            assert float(tx.amount) < 10000.0
    
    def test_apply_aml_violation_large_amount(self, sample_transaction, compliance_config):
        """Test AML large amount violation."""
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "large_amount": {
                    "enabled": True,
                    "frequency": 1.0,
                    "min_amount": 50000.0,
                }
            }
        )
        compliance_config.scenarios = {"aml_violations": scenario}
        generator = ComplianceViolationGenerator(compliance_config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(sample_transaction)
            
            assert "aml_large_amount" in violations
            assert float(tx.amount) >= 50000.0
    
    def test_apply_aml_violation_rapid_fire(self, sample_transaction, compliance_config):
        """Test AML rapid fire violation."""
        from datetime import timedelta
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "rapid_fire": {
                    "enabled": True,
                    "frequency": 1.0,
                }
            }
        )
        compliance_config.scenarios = {"aml_violations": scenario}
        generator = ComplianceViolationGenerator(compliance_config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(sample_transaction)
            
            assert "aml_rapid_fire" in violations
            # Timestamp should be very recent (within last 60 seconds)
            time_diff = (datetime.now() - tx.transaction_timestamp).total_seconds()
            assert time_diff >= 0  # Should be in the past
            assert time_diff < 120  # Allow some margin (within 2 minutes)
    
    def test_apply_kyc_violation_missing_customer_id(self, sample_transaction, compliance_config):
        """Test KYC missing customer ID violation."""
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "missing_customer_id": {
                    "enabled": True,
                    "frequency": 1.0,
                }
            }
        )
        compliance_config.scenarios = {"kyc_violations": scenario}
        generator = ComplianceViolationGenerator(compliance_config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(sample_transaction)
            
            assert "kyc_missing_customer_id" in violations
            assert tx.customer_id is None
    
    def test_apply_kyc_violation_invalid_email(self, sample_transaction, compliance_config):
        """Test KYC invalid email violation."""
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "invalid_email": {
                    "enabled": True,
                    "frequency": 1.0,
                }
            }
        )
        compliance_config.scenarios = {"kyc_violations": scenario}
        generator = ComplianceViolationGenerator(compliance_config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(sample_transaction)
            
            assert "kyc_invalid_email" in violations
            # Email should be set to invalid format (bypasses Pydantic validation)
            assert tx.customer_email == "invalid-email-format"
    
    def test_apply_pci_violation_missing_card_data(self, sample_transaction, compliance_config):
        """Test PCI missing card data violation."""
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
        compliance_config.scenarios = {"pci_violations": scenario}
        generator = ComplianceViolationGenerator(compliance_config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(sample_transaction)
            
            assert "pci_missing_card_data" in violations
    
    def test_apply_data_quality_violation_negative_amount(self, sample_transaction, compliance_config):
        """Test data quality negative amount violation."""
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "negative_amount": {
                    "enabled": True,
                    "frequency": 1.0,
                }
            }
        )
        compliance_config.scenarios = {"data_quality_violations": scenario}
        generator = ComplianceViolationGenerator(compliance_config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(sample_transaction)
            
            assert "data_quality_negative_amount" in violations
            assert float(tx.amount) < 0
    
    def test_apply_data_quality_violation_zero_amount(self, sample_transaction, compliance_config):
        """Test data quality zero amount violation."""
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={
                "zero_amount": {
                    "enabled": True,
                    "frequency": 1.0,
                }
            }
        )
        compliance_config.scenarios = {"data_quality_violations": scenario}
        generator = ComplianceViolationGenerator(compliance_config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(sample_transaction)
            
            assert "data_quality_zero_amount" in violations
            assert tx.amount == Decimal("0.00")
    
    def test_apply_business_rule_violation(self, sample_transaction, compliance_config):
        """Test business rule violation."""
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
        compliance_config.scenarios = {"business_rule_violations": scenario}
        generator = ComplianceViolationGenerator(compliance_config)
        
        # Set status to failed so the violation can change it
        sample_transaction.payment_status = "failed"
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(sample_transaction)
            
            assert "business_rule_status_mismatch" in violations
    
    def test_determine_severity(self, compliance_config):
        """Test severity determination."""
        generator = ComplianceViolationGenerator(compliance_config)
        
        # Test different violation types
        assert generator._determine_severity(["aml_large_amount"]) == "critical"
        assert generator._determine_severity(["aml_structuring"]) == "high"
        assert generator._determine_severity(["kyc_missing_customer_id"]) == "high"
        assert generator._determine_severity(["data_quality_negative_amount"]) == "medium"
        assert generator._determine_severity(["unknown_violation"]) == "low"
    
    def test_no_enabled_scenarios(self, sample_transaction, compliance_config):
        """Test when no scenarios are enabled."""
        compliance_config.scenarios = {}
        generator = ComplianceViolationGenerator(compliance_config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(sample_transaction)
            
            assert violations == []

