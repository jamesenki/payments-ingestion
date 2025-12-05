"""
Metrics collection for publishers.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
from collections import defaultdict


@dataclass
class PublisherMetrics:
    """
    Metrics tracking for publisher operations.
    """
    total_published: int = 0
    total_failed: int = 0
    total_batches: int = 0
    total_retries: int = 0
    publish_rate: float = 0.0  # transactions per second
    error_rate: float = 0.0  # errors per second
    average_latency_ms: float = 0.0
    last_publish_time: datetime = field(default_factory=datetime.now)
    errors_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    latency_history: List[float] = field(default_factory=list)
    
    def record_success(self, count: int = 1, latency_ms: float = 0.0):
        """Record a successful publish."""
        self.total_published += count
        self.last_publish_time = datetime.now()
        if latency_ms > 0:
            self.latency_history.append(latency_ms)
            # Keep only last 100 measurements
            if len(self.latency_history) > 100:
                self.latency_history.pop(0)
            self.average_latency_ms = sum(self.latency_history) / len(self.latency_history)
    
    def record_failure(self, error_type: str = "unknown", retry_count: int = 0):
        """Record a failed publish."""
        self.total_failed += 1
        self.errors_by_type[error_type] += 1
        if retry_count > 0:
            self.total_retries += retry_count
    
    def record_batch(self, size: int):
        """Record a batch publish."""
        self.total_batches += 1
    
    def calculate_rates(self, time_window_seconds: float = 60.0):
        """
        Calculate publish and error rates over a time window.
        
        Args:
            time_window_seconds: Time window for rate calculation
        """
        if time_window_seconds <= 0:
            return
        
        # Simple rate calculation (would be better with time-series data)
        # For now, use total published / elapsed time
        elapsed = (datetime.now() - self.last_publish_time).total_seconds()
        if elapsed > 0:
            self.publish_rate = self.total_published / elapsed
            self.error_rate = self.total_failed / elapsed
    
    def get_summary(self) -> Dict:
        """Get a summary of metrics."""
        self.calculate_rates()
        return {
            "total_published": self.total_published,
            "total_failed": self.total_failed,
            "total_batches": self.total_batches,
            "total_retries": self.total_retries,
            "publish_rate": self.publish_rate,
            "error_rate": self.error_rate,
            "average_latency_ms": self.average_latency_ms,
            "success_rate": (
                self.total_published / (self.total_published + self.total_failed)
                if (self.total_published + self.total_failed) > 0
                else 0.0
            ),
            "errors_by_type": dict(self.errors_by_type),
        }
    
    def reset(self):
        """Reset all metrics."""
        self.total_published = 0
        self.total_failed = 0
        self.total_batches = 0
        self.total_retries = 0
        self.publish_rate = 0.0
        self.error_rate = 0.0
        self.average_latency_ms = 0.0
        self.errors_by_type.clear()
        self.latency_history.clear()

