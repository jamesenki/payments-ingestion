"""
Unit tests for publisher classes.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from simulator.publishers.base import BasePublisher
from simulator.publishers.metrics import PublisherMetrics
from conftest import sample_transaction_dict


class MockPublisher(BasePublisher):
    """Mock publisher for testing base class."""
    
    async def publish(self, transaction):
        return True
    
    async def publish_batch(self, transactions):
        return len(transactions)
    
    async def close(self):
        pass


class TestBasePublisher:
    """Test BasePublisher abstract class."""
    
    def test_initialization(self):
        """Test publisher initialization."""
        config = {"batch_size": 50}
        publisher = MockPublisher(config)
        
        assert publisher.config == config
        assert publisher.batch_size == 50
        assert publisher.batch == []
    
    def test_default_batch_size(self):
        """Test default batch size."""
        config = {}
        publisher = MockPublisher(config)
        
        assert publisher.batch_size == 100  # Default
    
    def test_add_to_batch(self):
        """Test adding to batch."""
        config = {"batch_size": 5}
        publisher = MockPublisher(config)
        
        for i in range(4):
            result = publisher.add_to_batch({"id": i})
            assert result is True
        
        assert len(publisher.batch) == 4
    
    def test_add_to_batch_full(self):
        """Test batch auto-publish when full."""
        config = {"batch_size": 3}
        publisher = MockPublisher(config)
        
        publisher.add_to_batch({"id": 1})
        publisher.add_to_batch({"id": 2})
        result = publisher.add_to_batch({"id": 3})
        
        assert result is False  # Batch is full
        assert len(publisher.batch) == 3
    
    @pytest.mark.asyncio
    async def test_flush_batch_empty(self):
        """Test flushing empty batch."""
        publisher = MockPublisher({})
        count = await publisher.flush_batch()
        
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_flush_batch_with_items(self):
        """Test flushing batch with items."""
        publisher = MockPublisher({})
        publisher.batch = [{"id": 1}, {"id": 2}]
        
        count = await publisher.flush_batch()
        
        assert count == 2
        assert len(publisher.batch) == 0
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test context manager usage."""
        async with MockPublisher({}) as publisher:
            assert publisher is not None


class TestPublisherMetrics:
    """Test PublisherMetrics class."""
    
    def test_initialization(self):
        """Test metrics initialization."""
        metrics = PublisherMetrics()
        
        assert metrics.total_published == 0
        assert metrics.total_failed == 0
        assert metrics.total_batches == 0
    
    def test_record_success(self):
        """Test recording successful publish."""
        metrics = PublisherMetrics()
        metrics.record_success(count=5, latency_ms=10.0)
        
        assert metrics.total_published == 5
        assert len(metrics.latency_history) == 1
        assert metrics.average_latency_ms == 10.0
    
    def test_record_failure(self):
        """Test recording failed publish."""
        metrics = PublisherMetrics()
        metrics.record_failure(error_type="connection_error", retry_count=2)
        
        assert metrics.total_failed == 1
        assert metrics.errors_by_type["connection_error"] == 1
        assert metrics.total_retries == 2
    
    def test_record_batch(self):
        """Test recording batch."""
        metrics = PublisherMetrics()
        metrics.record_batch(size=100)
        
        assert metrics.total_batches == 1
    
    def test_calculate_rates(self):
        """Test rate calculation."""
        metrics = PublisherMetrics()
        metrics.total_published = 100
        metrics.total_failed = 5
        metrics.last_publish_time = datetime.now()
        
        metrics.calculate_rates(time_window_seconds=10.0)
        
        # Rates should be calculated
        assert metrics.publish_rate >= 0
        assert metrics.error_rate >= 0
    
    def test_get_summary(self):
        """Test getting metrics summary."""
        metrics = PublisherMetrics()
        metrics.record_success(count=100)
        metrics.record_failure(error_type="error", retry_count=1)
        metrics.record_batch(size=100)
        
        summary = metrics.get_summary()
        
        assert summary["total_published"] == 100
        assert summary["total_failed"] == 1
        assert summary["total_batches"] == 1
        assert "success_rate" in summary
        assert "errors_by_type" in summary
    
    def test_reset(self):
        """Test resetting metrics."""
        metrics = PublisherMetrics()
        metrics.record_success(count=10)
        metrics.record_failure()
        metrics.reset()
        
        assert metrics.total_published == 0
        assert metrics.total_failed == 0
        assert len(metrics.latency_history) == 0


class TestEventHubPublisher:
    """Test EventHubPublisher (with mocks)."""
    
    @pytest.mark.asyncio
    async def test_publisher_creation_without_azure(self):
        """Test publisher creation when Azure SDK not available."""
        from simulator.publishers.event_hub import EventHubPublisher
        
        config = {"batch_size": 100}
        
        # Mock Azure SDK not available
        with patch('simulator.publishers.event_hub.AZURE_EVENTHUB_AVAILABLE', False):
            # Should raise ImportError on creation
            with pytest.raises(ImportError):
                EventHubPublisher(config)
    
    @pytest.mark.asyncio
    async def test_publisher_with_mock_connection(self, mock_event_hub_connection_string):
        """Test publisher with mock connection string."""
        from simulator.publishers.event_hub import EventHubPublisher
        import os
        
        conn_str = os.getenv("EVENTHUB_CONNECTION_STRING", "")
        config = {
            "batch_size": 100,
            "connection_string": conn_str or "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test;EntityPath=test",
        }
        
        # Mock the Azure SDK
        with patch('simulator.publishers.event_hub.AZURE_EVENTHUB_AVAILABLE', True):
            try:
                publisher = EventHubPublisher(config)
                assert publisher is not None
                assert publisher.config is not None
            except ImportError:
                # If Azure SDK not actually available, skip this test
                pytest.skip("Azure SDK not available")

