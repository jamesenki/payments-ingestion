"""
Additional tests for BasePublisher to increase coverage to 90%+.

Tests context managers and edge cases that are currently uncovered.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from simulator.publishers.base import BasePublisher


class MockPublisher(BasePublisher):
    """Mock publisher for testing base class."""
    
    async def publish(self, transaction):
        return True
    
    async def publish_batch(self, transactions):
        return len(transactions)
    
    async def close(self):
        pass


class TestBasePublisherContextManagers:
    """Test BasePublisher context manager methods for full coverage."""
    
    def test_sync_context_manager_enter(self):
        """Test synchronous context manager __enter__."""
        publisher = MockPublisher({})
        result = publisher.__enter__()
        assert result is publisher
    
    def test_sync_context_manager_exit(self):
        """Test synchronous context manager __exit__."""
        publisher = MockPublisher({})
        # Should not raise, just pass through
        result = publisher.__exit__(None, None, None)
        assert result is None
    
    def test_sync_context_manager_exit_with_exception(self):
        """Test synchronous context manager __exit__ with exception."""
        publisher = MockPublisher({})
        # Should not suppress exception
        result = publisher.__exit__(ValueError, ValueError("test"), None)
        assert result is None  # Does not suppress
    
    @pytest.mark.asyncio
    async def test_async_context_manager_enter(self):
        """Test async context manager __aenter__."""
        publisher = MockPublisher({})
        result = await publisher.__aenter__()
        assert result is publisher
    
    @pytest.mark.asyncio
    async def test_async_context_manager_exit(self):
        """Test async context manager __aexit__ without batch."""
        publisher = MockPublisher({})
        publisher.batch = []  # Empty batch
        
        result = await publisher.__aexit__(None, None, None)
        assert result is None
        # close() should be called
        assert publisher.batch == []
    
    @pytest.mark.asyncio
    async def test_async_context_manager_exit_with_batch(self):
        """Test async context manager __aexit__ with batch to flush."""
        publisher = MockPublisher({})
        publisher.batch = [{"id": 1}, {"id": 2}]
        
        result = await publisher.__aexit__(None, None, None)
        assert result is None
        # Batch should be flushed (cleared)
        assert len(publisher.batch) == 0
    
    @pytest.mark.asyncio
    async def test_async_context_manager_exit_with_exception(self):
        """Test async context manager __aexit__ with exception."""
        publisher = MockPublisher({})
        publisher.batch = []
        
        # Should still close and flush even with exception
        result = await publisher.__aexit__(ValueError, ValueError("test"), None)
        assert result is None  # Does not suppress
    
    @pytest.mark.asyncio
    async def test_async_context_manager_exit_flush_error(self):
        """Test async context manager __aexit__ when flush fails."""
        publisher = MockPublisher({})
        publisher.batch = [{"id": 1}]
        
        # Mock publish_batch to raise error
        async def failing_publish_batch(transactions):
            raise RuntimeError("Publish failed")
        
        publisher.publish_batch = failing_publish_batch
        
        # Should still attempt to close
        with pytest.raises(RuntimeError):
            await publisher.__aexit__(None, None, None)
    
    @pytest.mark.asyncio
    async def test_async_context_manager_exit_close_error(self):
        """Test async context manager __aexit__ when close fails."""
        publisher = MockPublisher({})
        publisher.batch = []
        
        # Mock close to raise error
        async def failing_close():
            raise RuntimeError("Close failed")
        
        publisher.close = failing_close
        
        # Should propagate error
        with pytest.raises(RuntimeError):
            await publisher.__aexit__(None, None, None)
    
    @pytest.mark.asyncio
    async def test_context_manager_usage_sync(self):
        """Test using BasePublisher as sync context manager."""
        with MockPublisher({}) as publisher:
            assert publisher is not None
            assert isinstance(publisher, MockPublisher)
    
    @pytest.mark.asyncio
    async def test_context_manager_usage_async(self):
        """Test using BasePublisher as async context manager."""
        async with MockPublisher({}) as publisher:
            assert publisher is not None
            assert isinstance(publisher, MockPublisher)
            # Batch should be empty after exit
            assert publisher.batch == []


class TestBasePublisherEdgeCases:
    """Test edge cases for BasePublisher."""
    
    def test_add_to_batch_exactly_batch_size(self):
        """Test adding exactly batch_size items."""
        config = {"batch_size": 3}
        publisher = MockPublisher(config)
        
        # Add exactly batch_size items
        publisher.add_to_batch({"id": 1})
        publisher.add_to_batch({"id": 2})
        result = publisher.add_to_batch({"id": 3})
        
        assert result is False  # Batch is full
        assert len(publisher.batch) == 3
    
    @pytest.mark.asyncio
    async def test_flush_batch_clears_after_publish(self):
        """Test that flush_batch clears batch after publishing."""
        publisher = MockPublisher({})
        publisher.batch = [{"id": 1}, {"id": 2}, {"id": 3}]
        
        count = await publisher.flush_batch()
        
        assert count == 3
        assert len(publisher.batch) == 0
        # Verify batch is truly cleared
        assert publisher.batch == []
    
    @pytest.mark.asyncio
    async def test_flush_batch_multiple_times(self):
        """Test flushing batch multiple times."""
        publisher = MockPublisher({})
        
        # First flush (empty)
        count1 = await publisher.flush_batch()
        assert count1 == 0
        
        # Add items and flush
        publisher.batch = [{"id": 1}]
        count2 = await publisher.flush_batch()
        assert count2 == 1
        
        # Flush again (should be empty)
        count3 = await publisher.flush_batch()
        assert count3 == 0

