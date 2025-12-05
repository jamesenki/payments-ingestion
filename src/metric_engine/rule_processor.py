"""
Rule processing module for deriving metrics from transactions.
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from .models import NormalizedTransaction, DerivedMetric
from .utils.logger import get_logger


class RuleProcessor:
    """Processes rules to derive metrics from transactions."""
    
    def __init__(self, rules_file: str, rule_version: str = "1.0.0"):
        """
        Initialize rule processor.
        
        Args:
            rules_file: Path to YAML rules file
            rule_version: Version of rules to use
        """
        self.rules_file = rules_file
        self.rule_version = rule_version
        self.logger = get_logger("metric_engine.rule_processor")
        self.rules = []
        self._load_rules()
    
    def _load_rules(self):
        """Load rules from YAML file."""
        try:
            rules_path = Path(self.rules_file)
            if not rules_path.exists():
                # Try relative to config directory
                rules_path = Path(__file__).parent.parent.parent / "config" / "metric_rules.yaml"
            
            if not rules_path.exists():
                self.logger.warning(f"Rules file not found: {self.rules_file}")
                return
            
            with open(rules_path, 'r') as f:
                rules_data = yaml.safe_load(f)
            
            if rules_data and isinstance(rules_data, dict):
                self.rules = rules_data.get("rules", [])
            else:
                self.rules = []
            self.logger.info(f"Loaded {len(self.rules)} rules from {rules_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to load rules: {e}", exc_info=True)
            self.rules = []
    
    def process_transaction(
        self,
        transaction: NormalizedTransaction
    ) -> List[DerivedMetric]:
        """
        Process a transaction through all applicable rules.
        
        Args:
            transaction: Normalized transaction to process
            
        Returns:
            List of derived metrics
        """
        metrics = []
        
        for rule in self.rules:
            if not rule.get("enabled", True):
                continue
            
            try:
                metric = self._apply_rule(rule, transaction)
                if metric:
                    metrics.append(metric)
            except Exception as e:
                self.logger.warning(
                    f"Failed to apply rule {rule.get('name')} to transaction {transaction.transaction_id}: {e}",
                    exc_info=True
                )
        
        return metrics
    
    def _apply_rule(
        self,
        rule: Dict[str, Any],
        transaction: NormalizedTransaction
    ) -> Optional[DerivedMetric]:
        """Apply a single rule to a transaction."""
        # Check condition if present
        condition = rule.get("condition")
        if condition:
            if not self._evaluate_condition(condition, transaction):
                return None
        
        # Determine metric value based on metric type
        metric_type = rule.get("metric_type", "count")
        metric_value = self._calculate_metric_value(metric_type, rule, transaction)
        
        if metric_value is None:
            return None
        
        # Build metric name (may include placeholders)
        metric_name = self._build_metric_name(rule.get("metric_name", ""), transaction)
        
        return DerivedMetric(
            transaction_id=transaction.transaction_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_type=metric_type,
            metric_category=rule.get("metric_category"),
            rule_name=rule.get("name", "unknown"),
            rule_version=rule.get("rule_version", self.rule_version),
            context=self._build_context(rule, transaction)
        )
    
    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        transaction: NormalizedTransaction
    ) -> bool:
        """Evaluate a condition against a transaction."""
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        
        if not field:
            return True
        
        # Get field value from transaction
        field_value = getattr(transaction, field, None)
        if field_value is None:
            return False
        
        # Evaluate based on operator
        if operator == "==":
            return field_value == value
        elif operator == "!=":
            return field_value != value
        elif operator == ">":
            return Decimal(str(field_value)) > Decimal(str(value))
        elif operator == ">=":
            return Decimal(str(field_value)) >= Decimal(str(value))
        elif operator == "<":
            return Decimal(str(field_value)) < Decimal(str(value))
        elif operator == "<=":
            return Decimal(str(field_value)) <= Decimal(str(value))
        else:
            self.logger.warning(f"Unknown operator: {operator}")
            return False
    
    def _calculate_metric_value(
        self,
        metric_type: str,
        rule: Dict[str, Any],
        transaction: NormalizedTransaction
    ) -> Optional[Decimal]:
        """Calculate metric value based on type."""
        if metric_type == "count":
            return Decimal("1")
        
        elif metric_type == "sum":
            field = rule.get("field", "amount")
            value = getattr(transaction, field, None)
            if value is None:
                return None
            return Decimal(str(value))
        
        elif metric_type == "average":
            # Average is typically calculated over multiple transactions
            # For single transaction, return the value
            field = rule.get("field", "amount")
            value = getattr(transaction, field, None)
            if value is None:
                return None
            return Decimal(str(value))
        
        elif metric_type == "percentage":
            # Percentage is typically calculated over multiple transactions
            # For single transaction, return 100 if condition met, 0 otherwise
            return Decimal("100") if rule.get("condition") else Decimal("0")
        
        elif metric_type == "ratio":
            # Ratio is typically calculated over multiple transactions
            # For single transaction, return 1 if condition met, 0 otherwise
            return Decimal("1") if rule.get("condition") else Decimal("0")
        
        elif metric_type == "derived":
            # Custom derived metric - use field value
            field = rule.get("field", "amount")
            value = getattr(transaction, field, None)
            if value is None:
                return None
            return Decimal(str(value))
        
        else:
            self.logger.warning(f"Unknown metric type: {metric_type}")
            return None
    
    def _build_metric_name(
        self,
        template: str,
        transaction: NormalizedTransaction
    ) -> str:
        """Build metric name from template with placeholders."""
        name = template
        
        # Replace placeholders
        if "{payment_method}" in name:
            name = name.replace("{payment_method}", transaction.payment_method or "unknown")
        if "{currency}" in name:
            name = name.replace("{currency}", transaction.currency or "unknown")
        if "{customer_id}" in name:
            name = name.replace("{customer_id}", transaction.customer_id or "unknown")
        
        return name
    
    def _build_context(
        self,
        rule: Dict[str, Any],
        transaction: NormalizedTransaction
    ) -> Dict[str, Any]:
        """Build context dictionary for metric."""
        context = {
            "rule_name": rule.get("name"),
            "transaction_timestamp": transaction.transaction_timestamp.isoformat(),
            "payment_method": transaction.payment_method,
            "currency": transaction.currency,
            "payment_status": transaction.payment_status
        }
        
        # Add group_by fields if present
        group_by = rule.get("group_by")
        if group_by:
            group_value = getattr(transaction, group_by, None)
            if group_value:
                context["group_by"] = {group_by: group_value}
        
        return context

