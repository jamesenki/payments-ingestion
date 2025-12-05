"""
Data aggregation module for the metric engine.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from collections import defaultdict

from .models import NormalizedTransaction, AggregatedMetric, TimeWindow
from .utils.logger import get_logger


class Aggregator:
    """Aggregates transactions into metrics over time windows."""
    
    def __init__(
        self,
        dimensions: List[str],
        operations: List[str],
        time_window: TimeWindow
    ):
        """
        Initialize aggregator.
        
        Args:
            dimensions: List of dimension fields to group by
            operations: List of aggregation operations (sum, average, count, min, max)
            time_window: Time window for aggregation
        """
        self.dimensions = dimensions
        self.operations = operations
        self.time_window = time_window
        self.logger = get_logger("metric_engine.aggregator")
    
    def aggregate(
        self,
        transactions: List[NormalizedTransaction]
    ) -> List[AggregatedMetric]:
        """
        Aggregate transactions into metrics.
        
        Args:
            transactions: List of transactions to aggregate
            
        Returns:
            List of aggregated metrics
        """
        # Filter transactions within time window
        window_transactions = [
            tx for tx in transactions
            if self.time_window.contains(tx.transaction_timestamp)
        ]
        
        if not window_transactions:
            return []
        
        # Group by dimensions
        groups = self._group_by_dimensions(window_transactions)
        
        # Aggregate each group
        aggregated_metrics = []
        for dimension_values, group_transactions in groups.items():
            metric = self._aggregate_group(group_transactions, dimension_values)
            if metric:
                aggregated_metrics.append(metric)
        
        self.logger.info(
            f"Aggregated {len(window_transactions)} transactions into {len(aggregated_metrics)} metrics",
            extra={"extra_fields": {
                "window_start": self.time_window.start_time.isoformat(),
                "window_end": self.time_window.end_time.isoformat(),
                "dimensions": self.dimensions
            }}
        )
        
        return aggregated_metrics
    
    def _group_by_dimensions(
        self,
        transactions: List[NormalizedTransaction]
    ) -> Dict[tuple, List[NormalizedTransaction]]:
        """Group transactions by dimension values."""
        groups = defaultdict(list)
        
        for tx in transactions:
            dimension_values = tuple(
                getattr(tx, dim, "unknown") for dim in self.dimensions
            )
            groups[dimension_values].append(tx)
        
        return groups
    
    def _aggregate_group(
        self,
        transactions: List[NormalizedTransaction],
        dimension_values: tuple
    ) -> Optional[AggregatedMetric]:
        """Aggregate a group of transactions."""
        if not transactions:
            return None
        
        # Build dimensions dictionary
        dimensions_dict = {
            dim: value for dim, value in zip(self.dimensions, dimension_values)
        }
        
        # Calculate aggregations
        amounts = [tx.amount for tx in transactions]
        total_count = len(transactions)
        total_amount = sum(amounts)
        avg_amount = total_amount / total_count if total_count > 0 else None
        min_amount = min(amounts) if amounts else None
        max_amount = max(amounts) if amounts else None
        
        # Build additional metrics
        additional_metrics = {}
        
        # Status breakdown
        status_counts = defaultdict(int)
        for tx in transactions:
            status_counts[tx.payment_status] += 1
        
        additional_metrics["status_breakdown"] = dict(status_counts)
        
        # Payment method breakdown
        method_counts = defaultdict(int)
        for tx in transactions:
            method_counts[tx.payment_method] += 1
        
        additional_metrics["payment_method_breakdown"] = dict(method_counts)
        
        # Currency breakdown
        currency_counts = defaultdict(int)
        for tx in transactions:
            currency_counts[tx.currency] += 1
        
        additional_metrics["currency_breakdown"] = dict(currency_counts)
        
        # Unique customers and merchants
        unique_customers = len(set(tx.customer_id for tx in transactions if tx.customer_id))
        unique_merchants = len(set(tx.merchant_id for tx in transactions if tx.merchant_id))
        
        additional_metrics["unique_customers"] = unique_customers
        additional_metrics["unique_merchants"] = unique_merchants
        
        return AggregatedMetric(
            window_start=self.time_window.start_time,
            window_end=self.time_window.end_time,
            dimensions=dimensions_dict,
            total_count=total_count,
            total_amount=total_amount,
            avg_amount=avg_amount,
            min_amount=min_amount,
            max_amount=max_amount,
            additional_metrics=additional_metrics
        )

