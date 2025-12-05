"""
Data models for the metric engine.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class RawTransaction(BaseModel):
    """Raw transaction data from source."""
    
    transaction_id: str
    transaction_timestamp: datetime
    amount: Decimal
    currency: str
    payment_method: str
    payment_status: str
    customer_id: Optional[str] = None
    customer_email: Optional[str] = None
    customer_country: Optional[str] = None
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    transaction_type: Optional[str] = None
    channel: Optional[str] = None
    device_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(validate_assignment=True)


class NormalizedTransaction(BaseModel):
    """Normalized transaction with validated fields."""
    
    transaction_id: str
    transaction_timestamp: datetime
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    payment_method: str
    payment_status: str = Field(pattern="^(pending|completed|failed|cancelled|refunded)$")
    customer_id: Optional[str] = None
    customer_email: Optional[str] = None
    customer_country: Optional[str] = Field(None, min_length=2, max_length=2)
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    transaction_type: Optional[str] = None
    channel: Optional[str] = None
    device_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    normalized_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(validate_assignment=True)


class DerivedMetric(BaseModel):
    """Rule-derived metric from a transaction."""
    
    transaction_id: str
    metric_name: str
    metric_value: Decimal
    metric_type: str = Field(pattern="^(count|sum|average|ratio|percentage|derived)$")
    metric_category: Optional[str] = None
    rule_name: str
    rule_version: str
    context: Optional[Dict[str, Any]] = None
    calculated_at: datetime = Field(default_factory=datetime.now)
    effective_date: datetime = Field(default_factory=lambda: datetime.now().date)
    
    model_config = ConfigDict(validate_assignment=True)


class AggregatedMetric(BaseModel):
    """Aggregated metric over a time window."""
    
    window_start: datetime
    window_end: datetime
    dimensions: Dict[str, str]  # e.g., {"payment_method": "credit_card", "currency": "USD"}
    total_count: int = 0
    total_amount: Decimal = Decimal("0.00")
    avg_amount: Optional[Decimal] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    additional_metrics: Optional[Dict[str, Any]] = None
    calculated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(validate_assignment=True)


class Cluster(BaseModel):
    """Cluster of similar transactions."""
    
    cluster_id: int
    transaction_ids: List[str]
    centroid: Optional[Dict[str, Any]] = None
    size: int
    time_window_start: datetime
    time_window_end: datetime
    algorithm: str
    similarity_metric: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(validate_assignment=True)


class TimeWindow(BaseModel):
    """Time window definition."""
    
    name: str
    duration_seconds: int
    start_time: datetime
    end_time: datetime
    enabled: bool = True
    
    def contains(self, timestamp: datetime) -> bool:
        """Check if timestamp falls within this window."""
        return self.start_time <= timestamp < self.end_time
    
    model_config = ConfigDict(validate_assignment=True)

