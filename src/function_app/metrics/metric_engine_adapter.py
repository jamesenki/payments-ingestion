"""
Adapter to integrate MetricEngine with Azure Function processing.

This module bridges the gap between ParsedTransaction (from function app)
and MetricEngine's NormalizedTransaction/DerivedMetric models.
"""

import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from ...metric_engine.models import RawTransaction, NormalizedTransaction, DerivedMetric
from ...metric_engine.data_normalizer import DataNormalizer
from ...metric_engine.rule_processor import RuleProcessor
from ..parsing.models import ParsedTransaction

logger = logging.getLogger(__name__)


class MetricEngineAdapter:
    """
    Adapter to use MetricEngine for per-transaction metric extraction.
    
    This adapter:
    1. Converts ParsedTransaction to NormalizedTransaction
    2. Uses RuleProcessor to derive metrics
    3. Converts DerivedMetric to function app format
    """
    
    def __init__(self, rules_file: Optional[str] = None, rule_version: str = "1.0.0"):
        """
        Initialize the adapter.
        
        Args:
            rules_file: Path to metric rules YAML file (optional)
            rule_version: Version of rules to use
        """
        self.normalizer = DataNormalizer()
        self.rule_processor = RuleProcessor(
            rules_file=rules_file or "config/metric_rules.yaml",
            rule_version=rule_version
        )
        logger.info("MetricEngineAdapter initialized")
    
    def extract_metrics(self, transaction: ParsedTransaction) -> List[Dict[str, Any]]:
        """
        Extract metrics from a parsed transaction using MetricEngine.
        
        Args:
            transaction: Parsed transaction from function app
            
        Returns:
            List of metric dictionaries compatible with _store_dynamic_metrics()
        """
        try:
            # Convert ParsedTransaction to RawTransaction
            raw_transaction = self._parsed_to_raw(transaction)
            
            # Normalize the transaction
            normalized = self.normalizer.normalize(raw_transaction)
            if not normalized:
                logger.warning(
                    f"Failed to normalize transaction {transaction.transaction_id}, "
                    "falling back to basic metrics"
                )
                return self._fallback_metrics(transaction)
            
            # Process through rule processor
            derived_metrics = self.rule_processor.process_transaction(normalized)
            
            # Convert DerivedMetric to function app format
            metrics = self._derived_to_function_format(derived_metrics, transaction)
            
            # Always include basic metrics even if rules don't produce them
            if not any(m.get("metric_type") == "transaction_amount" for m in metrics):
                metrics.insert(0, {
                    "metric_type": "transaction_amount",
                    "metric_value": float(transaction.amount),
                    "metric_data": {
                        "currency": transaction.currency,
                        "status": str(transaction.status.value)
                    }
                })
            
            logger.debug(
                f"Extracted {len(metrics)} metrics for transaction {transaction.transaction_id}"
            )
            return metrics
            
        except Exception as e:
            logger.error(
                f"Error extracting metrics with MetricEngine: {e}, "
                f"falling back to basic metrics",
                exc_info=True
            )
            return self._fallback_metrics(transaction)
    
    def _parsed_to_raw(self, transaction: ParsedTransaction) -> RawTransaction:
        """Convert ParsedTransaction to RawTransaction."""
        # Extract payment method from metadata
        payment_method = transaction.metadata.get("payment_method", "unknown")
        
        # Extract payment status from transaction status
        payment_status_map = {
            "success": "completed",
            "failed": "failed",
            "pending": "pending"
        }
        payment_status = payment_status_map.get(
            str(transaction.status.value),
            str(transaction.status.value)
        )
        
        return RawTransaction(
            transaction_id=transaction.transaction_id,
            transaction_timestamp=transaction.timestamp,
            amount=Decimal(str(transaction.amount)),
            currency=transaction.currency,
            payment_method=payment_method,
            payment_status=payment_status,
            customer_id=transaction.customer_id,
            customer_email=transaction.metadata.get("customer_email"),
            customer_country=transaction.metadata.get("customer_country"),
            merchant_id=transaction.merchant_id,
            merchant_name=transaction.metadata.get("merchant_name"),
            merchant_category=transaction.metadata.get("merchant_category"),
            transaction_type=transaction.transaction_type,
            channel=transaction.channel,
            device_type=transaction.metadata.get("device_type"),
            metadata=transaction.metadata
        )
    
    def _derived_to_function_format(
        self,
        derived_metrics: List[DerivedMetric],
        transaction: ParsedTransaction
    ) -> List[Dict[str, Any]]:
        """Convert DerivedMetric objects to function app format."""
        metrics = []
        
        for derived in derived_metrics:
            metric_data = {
                "rule_name": derived.rule_name,
                "rule_version": derived.rule_version,
                "metric_category": derived.metric_category,
                "metric_type": derived.metric_type
            }
            
            # Add context if available
            if derived.context:
                metric_data.update(derived.context)
            
            metrics.append({
                "metric_type": derived.metric_name,  # Use metric_name as metric_type
                "metric_value": float(derived.metric_value),
                "metric_data": metric_data
            })
        
        return metrics
    
    def _fallback_metrics(self, transaction: ParsedTransaction) -> List[Dict[str, Any]]:
        """
        Fallback to basic metrics if MetricEngine fails.
        
        This provides the same basic metrics as the original _extract_metrics().
        """
        metrics = []
        
        # Basic transaction metrics
        metrics.append({
            "metric_type": "transaction_amount",
            "metric_value": float(transaction.amount),
            "metric_data": {
                "currency": transaction.currency,
                "status": str(transaction.status.value)
            }
        })
        
        # Channel metrics
        metrics.append({
            "metric_type": "channel_usage",
            "metric_value": 1,
            "metric_data": {
                "channel": transaction.channel,
                "transaction_type": transaction.transaction_type
            }
        })
        
        # Status metrics
        metrics.append({
            "metric_type": "transaction_status",
            "metric_value": 1,
            "metric_data": {
                "status": str(transaction.status.value),
                "transaction_type": transaction.transaction_type
            }
        })
        
        return metrics

