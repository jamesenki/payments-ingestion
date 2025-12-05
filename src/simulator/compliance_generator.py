"""
Compliance violation generator for creating out-of-compliance transactions.
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple, Optional

from .models import Transaction
from .config.schema import ComplianceConfig, ComplianceScenario


class ComplianceViolationGenerator:
    """
    Generates compliance violations for testing purposes.
    
    Supports:
    - AML violations (structuring, large amounts, rapid-fire)
    - KYC violations (missing/invalid customer data)
    - PCI violations (missing/invalid card data)
    - Data quality violations (invalid values, constraints)
    - Business rule violations (logical inconsistencies)
    """
    
    def __init__(self, config: ComplianceConfig):
        """
        Initialize compliance violation generator.
        
        Args:
            config: Compliance configuration
        """
        self.config = config
        self.violation_history: List[Dict] = []  # Track violations for patterns
    
    def should_apply_violation(self) -> bool:
        """
        Determine if this transaction should have a violation.
        
        Returns:
            True if violation should be applied
        """
        if not self.config.enabled:
            return False
        
        return random.random() < self.config.total_violation_percentage
    
    def apply_violation(
        self,
        transaction: Transaction,
        scenarios: Optional[Dict[str, ComplianceScenario]] = None
    ) -> Tuple[Transaction, List[str]]:
        """
        Apply a random compliance violation to a transaction.
        
        Args:
            transaction: Transaction to modify
            scenarios: Compliance scenarios configuration
            
        Returns:
            Tuple of (modified transaction, list of violation types)
        """
        if not self.should_apply_violation():
            return transaction, []
        
        violations = []
        
        if scenarios is None:
            scenarios = self.config.scenarios
        
        # Select which scenario to apply
        enabled_scenarios = {
            name: scenario
            for name, scenario in scenarios.items()
            if scenario.enabled and random.random() < scenario.percentage
        }
        
        if not enabled_scenarios:
            return transaction, []
        
        # Randomly select a scenario
        scenario_name = random.choice(list(enabled_scenarios.keys()))
        scenario = enabled_scenarios[scenario_name]
        
        # Apply violation based on scenario type
        if scenario_name == "aml_violations":
            transaction, violation = self._apply_aml_violation(transaction, scenario)
            violations.append(violation)
        
        elif scenario_name == "kyc_violations":
            transaction, violation = self._apply_kyc_violation(transaction, scenario)
            violations.append(violation)
        
        elif scenario_name == "pci_violations":
            transaction, violation = self._apply_pci_violation(transaction, scenario)
            violations.append(violation)
        
        elif scenario_name == "data_quality_violations":
            transaction, violation = self._apply_data_quality_violation(transaction, scenario)
            violations.append(violation)
        
        elif scenario_name == "business_rule_violations":
            transaction, violation = self._apply_business_rule_violation(transaction, scenario)
            violations.append(violation)
        
        # Record violation
        transaction.compliance_violations = violations
        transaction.violation_severity = self._determine_severity(violations)
        
        return transaction, violations
    
    def _apply_aml_violation(
        self,
        transaction: Transaction,
        scenario: ComplianceScenario
    ) -> Tuple[Transaction, str]:
        """Apply AML violation pattern."""
        patterns = scenario.patterns
        
        # Select pattern
        enabled_patterns = [
            name for name, pattern in patterns.items()
            if pattern.enabled and random.random() < pattern.frequency
        ]
        
        if not enabled_patterns:
            return transaction, "aml_unknown"
        
        pattern_name = random.choice(enabled_patterns)
        pattern = patterns[pattern_name]
        
        if pattern_name == "structuring":
            # Multiple transactions just under threshold
            threshold = float(pattern.threshold) if pattern.threshold else 10000.0
            # Set amount to just under threshold
            transaction.amount = Decimal(str(threshold - random.uniform(1, 100)))
            return transaction, "aml_structuring"
        
        elif pattern_name == "large_amount":
            # Suspiciously large amount
            min_amount = float(pattern.min_amount) if pattern.min_amount else 50000.0
            transaction.amount = Decimal(str(random.uniform(min_amount, min_amount * 2)))
            return transaction, "aml_large_amount"
        
        elif pattern_name == "rapid_fire":
            # Very recent timestamp (rapid-fire transactions)
            transaction.transaction_timestamp = datetime.now() - timedelta(seconds=random.randint(1, 60))
            return transaction, "aml_rapid_fire"
        
        return transaction, "aml_unknown"
    
    def _apply_kyc_violation(
        self,
        transaction: Transaction,
        scenario: ComplianceScenario
    ) -> Tuple[Transaction, str]:
        """Apply KYC violation pattern."""
        patterns = scenario.patterns
        
        enabled_patterns = [
            name for name, pattern in patterns.items()
            if pattern.enabled and random.random() < pattern.frequency
        ]
        
        if not enabled_patterns:
            return transaction, "kyc_unknown"
        
        pattern_name = random.choice(enabled_patterns)
        
        if pattern_name == "missing_customer_id":
            transaction.customer_id = None
            return transaction, "kyc_missing_customer_id"
        
        elif pattern_name == "invalid_email":
            # Bypass validation by directly setting the attribute
            object.__setattr__(transaction, "customer_email", "invalid-email-format")
            return transaction, "kyc_invalid_email"
        
        elif pattern_name == "missing_country":
            transaction.customer_country = None
            return transaction, "kyc_missing_country"
        
        return transaction, "kyc_unknown"
    
    def _apply_pci_violation(
        self,
        transaction: Transaction,
        scenario: ComplianceScenario
    ) -> Tuple[Transaction, str]:
        """Apply PCI violation pattern."""
        patterns = scenario.patterns
        
        enabled_patterns = [
            name for name, pattern in patterns.items()
            if pattern.enabled and random.random() < pattern.frequency
        ]
        
        if not enabled_patterns:
            return transaction, "pci_unknown"
        
        pattern_name = random.choice(enabled_patterns)
        
        if pattern_name == "missing_card_data":
            # Remove card data from metadata
            if "card_last4" in transaction.metadata:
                del transaction.metadata["card_last4"]
            if "card_brand" in transaction.metadata:
                del transaction.metadata["card_brand"]
            return transaction, "pci_missing_card_data"
        
        elif pattern_name == "invalid_card_brand":
            transaction.metadata["card_brand"] = "InvalidBrand"
            return transaction, "pci_invalid_card_brand"
        
        return transaction, "pci_unknown"
    
    def _apply_data_quality_violation(
        self,
        transaction: Transaction,
        scenario: ComplianceScenario
    ) -> Tuple[Transaction, str]:
        """Apply data quality violation pattern."""
        patterns = scenario.patterns
        
        enabled_patterns = [
            name for name, pattern in patterns.items()
            if pattern.enabled and random.random() < pattern.frequency
        ]
        
        if not enabled_patterns:
            return transaction, "data_quality_unknown"
        
        pattern_name = random.choice(enabled_patterns)
        
        if pattern_name == "negative_amount":
            # Bypass validation by directly setting the attribute
            object.__setattr__(transaction, "amount", Decimal("-100.00"))
            return transaction, "data_quality_negative_amount"
        
        elif pattern_name == "zero_amount":
            # Bypass validation by directly setting the attribute
            object.__setattr__(transaction, "amount", Decimal("0.00"))
            return transaction, "data_quality_zero_amount"
        
        elif pattern_name == "invalid_currency":
            transaction.currency = "XXX"  # Invalid currency code
            return transaction, "data_quality_invalid_currency"
        
        elif pattern_name == "invalid_status":
            transaction.payment_status = "processing"  # Not in allowed list
            return transaction, "data_quality_invalid_status"
        
        elif pattern_name == "future_timestamp":
            transaction.transaction_timestamp = datetime.now() + timedelta(days=1)
            return transaction, "data_quality_future_timestamp"
        
        return transaction, "data_quality_unknown"
    
    def _apply_business_rule_violation(
        self,
        transaction: Transaction,
        scenario: ComplianceScenario
    ) -> Tuple[Transaction, str]:
        """Apply business rule violation pattern."""
        patterns = scenario.patterns
        
        enabled_patterns = [
            name for name, pattern in patterns.items()
            if pattern.enabled and random.random() < pattern.frequency
        ]
        
        if not enabled_patterns:
            return transaction, "business_rule_unknown"
        
        pattern_name = random.choice(enabled_patterns)
        
        if pattern_name == "status_mismatch":
            # Failed transaction marked as completed
            if transaction.payment_status == "failed":
                transaction.payment_status = "completed"
            return transaction, "business_rule_status_mismatch"
        
        elif pattern_name == "orphan_refund":
            # Refund without original transaction
            transaction.payment_status = "refunded"
            transaction.transaction_type = "refund"
            # No reference to original transaction
            return transaction, "business_rule_orphan_refund"
        
        elif pattern_name == "currency_mismatch":
            # Currency doesn't match country
            if transaction.customer_country == "US":
                transaction.currency = "EUR"  # Wrong currency
            return transaction, "business_rule_currency_mismatch"
        
        return transaction, "business_rule_unknown"
    
    def _determine_severity(self, violations: List[str]) -> str:
        """Determine violation severity based on violation types."""
        critical_violations = ["aml_large_amount", "pci_missing_card_data"]
        high_violations = ["aml_structuring", "kyc_missing_customer_id"]
        medium_violations = ["data_quality_negative_amount", "data_quality_zero_amount"]
        
        for violation in violations:
            if violation in critical_violations:
                return "critical"
            if violation in high_violations:
                return "high"
            if violation in medium_violations:
                return "medium"
        
        return "low"

