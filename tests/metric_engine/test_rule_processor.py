"""
Unit tests for rule processor.
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch, mock_open

from src.metric_engine.rule_processor import RuleProcessor
from src.metric_engine.models import NormalizedTransaction, DerivedMetric


class TestRuleProcessor:
    """Tests for RuleProcessor."""
    
    @pytest.fixture
    def sample_rules_yaml(self):
        """Sample rules YAML content."""
        return """rules:
  version: "1.0.0"
  - name: "high_value_transaction_count"
    description: "Count transactions above threshold"
    enabled: true
    metric_name: "high_value_count"
    metric_type: "count"
    metric_category: "transaction_volume"
    condition:
      field: "amount"
      operator: ">"
      value: 1000.00
    rule_version: "1.0.0"
  - name: "failed_transaction_percentage"
    description: "Calculate percentage of failed transactions"
    enabled: true
    metric_name: "failed_percentage"
    metric_type: "percentage"
    metric_category: "transaction_quality"
    condition:
      field: "payment_status"
      operator: "=="
      value: "failed"
    rule_version: "1.0.0"
  - name: "avg_amount_by_method"
    description: "Calculate average by payment method"
    enabled: true
    metric_name: "avg_amount_{payment_method}"
    metric_type: "average"
    metric_category: "transaction_amount"
    group_by: "payment_method"
    field: "amount"
    rule_version: "1.0.0"
"""
    
    @pytest.fixture
    def rule_processor(self, sample_rules_yaml, tmp_path):
        """Create a RuleProcessor with temporary rules file."""
        rules_file = tmp_path / "metric_rules.yaml"
        rules_file.write_text(sample_rules_yaml)
        
        return RuleProcessor(
            rules_file=str(rules_file),
            rule_version="1.0.0"
        )
    
    def test_load_rules(self, rule_processor):
        """Test loading rules from YAML file."""
        assert len(rule_processor.rules) == 3
        assert rule_processor.rules[0]["name"] == "high_value_transaction_count"
    
    def test_load_rules_file_not_found(self):
        """Test handling missing rules file."""
        processor = RuleProcessor(
            rules_file="nonexistent.yaml",
            rule_version="1.0.0"
        )
        # Should not raise, but have empty rules
        assert processor.rules == []
    
    def test_process_transaction_high_value(self, rule_processor, sample_normalized_transaction):
        """Test processing transaction that matches high value rule."""
        # Set high amount
        sample_normalized_transaction.amount = Decimal("2000.00")
        
        metrics = rule_processor.process_transaction(sample_normalized_transaction)
        
        # Should have at least one metric (high_value_count)
        assert len(metrics) > 0
        high_value_metric = next((m for m in metrics if m.metric_name == "high_value_count"), None)
        assert high_value_metric is not None
        assert high_value_metric.metric_type == "count"
    
    def test_process_transaction_low_value(self, rule_processor, sample_normalized_transaction):
        """Test processing transaction that doesn't match high value rule."""
        # Set low amount
        sample_normalized_transaction.amount = Decimal("100.00")
        
        metrics = rule_processor.process_transaction(sample_normalized_transaction)
        
        # Should not have high_value_count metric
        high_value_metric = next((m for m in metrics if m.metric_name == "high_value_count"), None)
        assert high_value_metric is None
    
    def test_process_transaction_failed_status(self, rule_processor):
        """Test processing failed transaction."""
        tx = NormalizedTransaction(
            transaction_id="tx-123",
            transaction_timestamp=datetime.now(),
            amount=Decimal("100.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="failed"
        )
        
        metrics = rule_processor.process_transaction(tx)
        
        # Should have failed_percentage metric
        failed_metric = next((m for m in metrics if m.metric_name == "failed_percentage"), None)
        assert failed_metric is not None
    
    def test_evaluate_condition_equals(self, rule_processor, sample_normalized_transaction):
        """Test condition evaluation with == operator."""
        condition = {
            "field": "payment_status",
            "operator": "==",
            "value": "completed"
        }
        
        result = rule_processor._evaluate_condition(condition, sample_normalized_transaction)
        assert result is True
    
    def test_evaluate_condition_not_equals(self, rule_processor, sample_normalized_transaction):
        """Test condition evaluation with != operator."""
        condition = {
            "field": "payment_status",
            "operator": "!=",
            "value": "failed"
        }
        
        result = rule_processor._evaluate_condition(condition, sample_normalized_transaction)
        assert result is True
    
    def test_evaluate_condition_greater_than(self, rule_processor, sample_normalized_transaction):
        """Test condition evaluation with > operator."""
        condition = {
            "field": "amount",
            "operator": ">",
            "value": 50.00
        }
        
        sample_normalized_transaction.amount = Decimal("100.00")
        result = rule_processor._evaluate_condition(condition, sample_normalized_transaction)
        assert result is True
    
    def test_evaluate_condition_less_than(self, rule_processor, sample_normalized_transaction):
        """Test condition evaluation with < operator."""
        condition = {
            "field": "amount",
            "operator": "<",
            "value": 200.00
        }
        
        sample_normalized_transaction.amount = Decimal("100.00")
        result = rule_processor._evaluate_condition(condition, sample_normalized_transaction)
        assert result is True
    
    def test_calculate_metric_value_count(self, rule_processor, sample_normalized_transaction):
        """Test calculating count metric value."""
        rule = {"metric_type": "count"}
        value = rule_processor._calculate_metric_value("count", rule, sample_normalized_transaction)
        assert value == Decimal("1")
    
    def test_calculate_metric_value_sum(self, rule_processor, sample_normalized_transaction):
        """Test calculating sum metric value."""
        rule = {"metric_type": "sum", "field": "amount"}
        sample_normalized_transaction.amount = Decimal("100.00")
        value = rule_processor._calculate_metric_value("sum", rule, sample_normalized_transaction)
        assert value == Decimal("100.00")
    
    def test_build_metric_name_with_placeholder(self, rule_processor, sample_normalized_transaction):
        """Test building metric name with placeholders."""
        template = "avg_amount_{payment_method}"
        name = rule_processor._build_metric_name(template, sample_normalized_transaction)
        assert "{payment_method}" not in name
        assert "credit_card" in name
    
    def test_build_context(self, rule_processor, sample_normalized_transaction):
        """Test building context dictionary."""
        rule = {
            "name": "test_rule",
            "group_by": "payment_method"
        }
        
        context = rule_processor._build_context(rule, sample_normalized_transaction)
        
        assert "rule_name" in context
        assert "transaction_timestamp" in context
        assert "payment_method" in context
        assert "group_by" in context
    
    def test_process_transaction_disabled_rule(self, rule_processor, sample_normalized_transaction):
        """Test that disabled rules are not applied."""
        # Disable first rule
        rule_processor.rules[0]["enabled"] = False
        
        metrics = rule_processor.process_transaction(sample_normalized_transaction)
        
        # Should not have metric from disabled rule
        high_value_metric = next((m for m in metrics if m.metric_name == "high_value_count"), None)
        assert high_value_metric is None

