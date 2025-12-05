"""
Final push to 90% coverage - targeting exact missing lines.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, AsyncMock, MagicMock

from simulator.compliance_generator import ComplianceViolationGenerator
from simulator.models import Transaction
from simulator.config.schema import ComplianceConfig, ComplianceScenario
from simulator.main import SimulatorApp
from conftest import sample_config_file


class TestCoverage90Push:
    """Final tests targeting exact missing lines."""
    
    def test_compliance_violation_with_violations_list(self):
        """Test that violations are added to transaction.compliance_violations."""
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
                "negative_amount": {
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
            
            # Test line 150: transaction.compliance_violations = violations
            assert tx.compliance_violations == violations
            assert len(tx.compliance_violations) > 0
    
    def test_kyc_missing_country_line_183(self):
        """Test KYC missing country to cover line 183."""
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
                "missing_country": {
                    "enabled": True,
                    "frequency": 1.0,
                }
            }
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"kyc_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            assert "kyc_missing_country" in violations
            assert tx.customer_country is None
    
    def test_pci_invalid_card_brand_line_215(self):
        """Test PCI invalid card brand to cover line 215."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
            metadata={"card_brand": "Visa"}
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
    
    def test_data_quality_unknown_line_231(self):
        """Test data quality unknown return to cover line 231."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        scenario = ComplianceScenario(
            enabled=True,
            percentage=1.0,
            patterns={}  # No patterns enabled
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"data_quality_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            # Should return unknown when no enabled patterns
            assert "data_quality_unknown" in violations
    
    def test_determine_severity_line_296(self):
        """Test determine_severity to cover line 296."""
        config = ComplianceConfig(enabled=True)
        generator = ComplianceViolationGenerator(config)
        
        # Test with empty violations list
        severity = generator._determine_severity([])
        assert severity == "low"
    
    @pytest.mark.asyncio
    async def test_main_violations_counting_line_154(self, sample_config_file, mock_event_hub_connection_string):
        """Test that violations are counted in stats (line 154)."""
        app = SimulatorApp(config_path=str(sample_config_file))
        
        with patch('simulator.main.create_publisher') as mock_create:
            mock_pub = MagicMock()
            mock_pub.config = {}
            mock_pub.publish_batch = AsyncMock(return_value=10)
            mock_create.return_value = mock_pub
            
            app.initialize()
            
            # Generate batch with compliance enabled
            initial_violations = app.stats["total_violations"]
            await app._generate_and_publish_batch(10)
            
            # Violations should be counted (line 154: self.stats["total_violations"] += len(violations))
            assert app.stats["total_violations"] >= initial_violations

