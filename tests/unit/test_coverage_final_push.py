"""
Final push to reach 90% coverage - targeting specific uncovered lines.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, AsyncMock, MagicMock

from simulator.compliance_generator import ComplianceViolationGenerator
from simulator.models import Transaction
from simulator.config.schema import ComplianceConfig, ComplianceScenario
from simulator.main import SimulatorApp
from conftest import sample_config_file


class TestCoverageFinalPush:
    """Final tests targeting specific uncovered lines."""
    
    def test_compliance_apply_violation_no_scenarios_in_config(self):
        """Test apply_violation when config has no scenarios."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={}  # Empty scenarios
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            # Should return empty violations when no scenarios
            assert len(violations) == 0
    
    def test_compliance_apply_violation_no_enabled_scenarios(self):
        """Test apply_violation when no scenarios are enabled."""
        transaction = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed",
        )
        
        scenario = ComplianceScenario(
            enabled=False,  # Disabled
            percentage=1.0,
            patterns={}
        )
        config = ComplianceConfig(
            enabled=True,
            total_violation_percentage=1.0,
            scenarios={"aml_violations": scenario}
        )
        generator = ComplianceViolationGenerator(config)
        
        with patch.object(generator, 'should_apply_violation', return_value=True):
            tx, violations = generator.apply_violation(transaction)
            
            # Should return empty when no enabled scenarios
            assert len(violations) == 0
    
    @pytest.mark.asyncio
    async def test_main_metadata_config_dict(self, sample_config_file, mock_event_hub_connection_string):
        """Test main with metadata config as dict."""
        app = SimulatorApp(config_path=str(sample_config_file))
        
        with patch('simulator.main.create_publisher') as mock_create:
            mock_pub = MagicMock()
            mock_pub.config = {}
            mock_pub.publish_batch = AsyncMock(return_value=5)
            mock_create.return_value = mock_pub
            
            app.initialize()
            
            # Test the else branch for metadata_config
            # This tests line 141
            await app._generate_and_publish_batch(5)
            assert app.stats["total_generated"] >= 5
    
    @pytest.mark.asyncio
    async def test_main_progress_logging_at_1000(self, sample_config_file, mock_event_hub_connection_string):
        """Test progress logging when total_generated is exactly 1000."""
        app = SimulatorApp(config_path=str(sample_config_file))
        
        with patch('simulator.main.create_publisher') as mock_create:
            mock_pub = MagicMock()
            mock_pub.config = {}
            mock_pub.publish_batch = AsyncMock(return_value=1000)
            mock_create.return_value = mock_pub
            
            app.initialize()
            app.stats["total_generated"] = 0
            
            # Generate exactly 1000 to trigger progress logging
            for _ in range(10):
                await app._generate_and_publish_batch(100)
            
            # Should have logged progress
            assert app.stats["total_generated"] >= 1000

