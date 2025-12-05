"""
Unit tests for main orchestrator.
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, timedelta

from src.metric_engine.main import MetricEngine
from src.metric_engine.models import NormalizedTransaction


class TestMetricEngine:
    """Tests for MetricEngine."""
    
    @pytest.fixture
    def sample_config(self, tmp_path):
        """Create a sample configuration file."""
        config = {
            "metric_engine": {
                "data_source": {
                    "type": "postgresql",
                    "connection_string": "postgresql://test:test@localhost/test",
                    "batch_size": 1000,
                    "max_retries": 3,
                    "retry_delay_seconds": 5
                },
                "time_windows": [
                    {"name": "5min", "duration_seconds": 300, "enabled": True},
                    {"name": "hourly", "duration_seconds": 3600, "enabled": True}
                ],
                "aggregation": {
                    "enabled": True,
                    "dimensions": ["payment_method", "currency"],
                    "operations": ["sum", "average", "count"],
                    "default_time_window": "5min"
                },
                "clustering": {
                    "enabled": True,
                    "algorithm": "kmeans",
                    "n_clusters": 5,
                    "time_window": "hourly"
                },
                "rules": {
                    "enabled": True,
                    "rules_file": "config/metric_rules.yaml",
                    "rule_version": "1.0.0"
                }
            },
            "logging": {
                "level": "INFO",
                "format": "json"
            }
        }
        
        config_file = tmp_path / "metric_engine_settings.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        return str(config_file)
    
    @pytest.fixture
    def sample_transactions(self):
        """Create sample transactions."""
        base_time = datetime.now()
        transactions = []
        
        for i in range(5):
            transactions.append(
                NormalizedTransaction(
                    transaction_id=f"tx-{i}",
                    transaction_timestamp=base_time + timedelta(minutes=i),
                    amount=Decimal(f"{100 + i * 10}.00"),
                    currency="USD",
                    payment_method="credit_card" if i % 2 == 0 else "debit_card",
                    payment_status="completed",
                    customer_id=f"cust-{i}"
                )
            )
        
        return transactions
    
    @patch('metric_engine.main.DataExtractor')
    @patch('metric_engine.main.RuleProcessor')
    def test_initialize_components(self, mock_rule_processor, mock_extractor, sample_config):
        """Test that all components are initialized."""
        engine = MetricEngine(config_path=sample_config)
        
        assert engine.extractor is not None
        assert engine.normalizer is not None
        assert engine.rule_processor is not None
        assert engine.time_window_manager is not None
    
    @patch('metric_engine.main.DataExtractor')
    @patch('metric_engine.main.RuleProcessor')
    def test_process_time_window(self, mock_rule_processor, mock_extractor, sample_config, sample_transactions):
        """Test processing a time window."""
        # Setup mocks
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.extract_transactions.return_value = [
            MagicMock() for _ in range(5)  # Raw transactions
        ]
        mock_extractor.return_value = mock_extractor_instance
        
        mock_rule_processor_instance = MagicMock()
        mock_rule_processor_instance.process_transaction.return_value = []
        mock_rule_processor.return_value = mock_rule_processor_instance
        
        engine = MetricEngine(config_path=sample_config)
        engine.normalizer.normalize_batch = Mock(return_value=sample_transactions)
        
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        results = engine.process_time_window("5min", start_time, end_time)
        
        assert "transactions_processed" in results
        assert "metrics_derived" in results
        assert "aggregated_metrics" in results
        assert "clusters" in results
    
    @patch('metric_engine.main.DataExtractor')
    @patch('metric_engine.main.RuleProcessor')
    def test_process_time_window_no_transactions(self, mock_rule_processor, mock_extractor, sample_config):
        """Test processing time window with no transactions."""
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.extract_transactions.return_value = []
        mock_extractor.return_value = mock_extractor_instance
        
        engine = MetricEngine(config_path=sample_config)
        
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        results = engine.process_time_window("5min", start_time, end_time)
        
        assert results["transactions_processed"] == 0
        assert results["metrics_derived"] == 0
    
    @patch('metric_engine.main.DataExtractor')
    @patch('metric_engine.main.RuleProcessor')
    def test_process_recent_transactions(self, mock_rule_processor, mock_extractor, sample_config):
        """Test processing recent transactions."""
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.extract_transactions.return_value = []
        mock_extractor.return_value = mock_extractor_instance
        
        engine = MetricEngine(config_path=sample_config)
        engine.process_time_window = Mock(return_value={
            "transactions_processed": 10,
            "metrics_derived": 5,
            "aggregated_metrics": 2,
            "clusters": 1
        })
        
        results = engine.process_recent_transactions(hours=1, window_name="5min")
        
        assert results["transactions_processed"] == 10
        engine.process_time_window.assert_called_once()
    
    @patch('metric_engine.main.DataExtractor')
    @patch('metric_engine.main.RuleProcessor')
    def test_close(self, mock_rule_processor, mock_extractor, sample_config):
        """Test closing the engine."""
        mock_extractor_instance = MagicMock()
        mock_extractor.return_value = mock_extractor_instance
        
        engine = MetricEngine(config_path=sample_config)
        engine.close()
        
        mock_extractor_instance.close.assert_called_once()

