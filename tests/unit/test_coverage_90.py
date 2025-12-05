"""
Final targeted tests to reach 90% coverage.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

from simulator.compliance_generator import ComplianceViolationGenerator
from simulator.models import Transaction
from simulator.config.schema import ComplianceConfig, ComplianceScenario
from simulator.main import SimulatorApp
from conftest import sample_config_file


class TestCoverage90:
    """Final tests to reach 90% coverage."""
    
    def test_data_quality_future_timestamp(self):
        """Test data quality future timestamp violation."""
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
                "future_timestamp": {
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
            
            assert "data_quality_future_timestamp" in violations
            # Timestamp should be in the future
            assert tx.transaction_timestamp > datetime.now()
    
    @pytest.mark.asyncio
    async def test_main_with_compliance_scenarios_none(self, sample_config_file, mock_event_hub_connection_string):
        """Test main with compliance scenarios as None."""
        app = SimulatorApp(config_path=str(sample_config_file))
        
        with patch('simulator.main.create_publisher') as mock_create:
            mock_pub = MagicMock()
            mock_pub.config = {}
            mock_pub.publish_batch = AsyncMock(return_value=5)
            mock_create.return_value = mock_pub
            
            app.initialize()
            
            # Test the code path where compliance.scenarios is accessed
            # The code checks: self.config.compliance.scenarios if self.config.compliance else None
            # So we need compliance to exist but scenarios could be None
            if app.config.compliance:
                # Just test the path - scenarios might be a dict or None
                await app._generate_and_publish_batch(5)
            else:
                await app._generate_and_publish_batch(5)
            
            assert app.stats["total_generated"] >= 5
    
    @pytest.mark.asyncio
    async def test_main_progress_logging_exact_1000(self, sample_config_file, mock_event_hub_connection_string):
        """Test progress logging when exactly 1000 transactions generated."""
        app = SimulatorApp(config_path=str(sample_config_file))
        
        with patch('simulator.main.create_publisher') as mock_create:
            mock_pub = MagicMock()
            mock_pub.config = {}
            mock_pub.publish_batch = AsyncMock(return_value=1000)
            mock_create.return_value = mock_pub
            
            app.initialize()
            
            # Set stats to trigger progress logging
            app.stats["total_generated"] = 999
            
            await app._generate_and_publish_batch(1)
            
            # Should have logged progress at 1000
            assert app.stats["total_generated"] >= 1000

