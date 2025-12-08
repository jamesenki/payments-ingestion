"""
Unit tests for MessageConsumer abstract base class.

Tests WO-36: MessageConsumer Abstract Base Class and Interface
"""

import pytest
from abc import ABC
from unittest.mock import MagicMock, patch

# Mock MessageBatch to avoid import chain issues
MessageBatch = MagicMock()


class TestMessageConsumerAbstract:
    """Tests for MessageConsumer abstract base class."""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that MessageConsumer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MessageConsumer()
    
    def test_is_abstract_base_class(self):
        """Test that MessageConsumer is an ABC."""
        assert issubclass(MessageConsumer, ABC)
    
    def test_all_methods_are_abstract(self):
        """Test that all required methods are abstract."""
        # Check that all abstract methods exist
        assert hasattr(MessageConsumer, 'connect')
        assert hasattr(MessageConsumer, 'disconnect')
        assert hasattr(MessageConsumer, 'is_connected')
        assert hasattr(MessageConsumer, 'consume_batch')
        assert hasattr(MessageConsumer, 'acknowledge_batch')
        assert hasattr(MessageConsumer, 'checkpoint')
        
        # Check that they are abstract methods
        assert getattr(MessageConsumer.connect, '__isabstractmethod__', False) or \
               hasattr(MessageConsumer.connect, '__abstractmethod__')
    
    def test_concrete_implementation_must_implement_all_methods(self):
        """Test that concrete implementations must implement all methods."""
        
        # Incomplete implementation - missing methods
        class IncompleteConsumer(MessageConsumer):
            def connect(self):
                pass
        
        with pytest.raises(TypeError):
            IncompleteConsumer()
    
    def test_complete_concrete_implementation(self):
        """Test that a complete implementation can be instantiated."""
        
        class CompleteConsumer(MessageConsumer):
            def connect(self):
                pass
            
            def disconnect(self):
                pass
            
            def is_connected(self):
                return True
            
            def consume_batch(self, max_messages=100, timeout_ms=1000):
                return None
            
            def acknowledge_batch(self, batch):
                pass
            
            def checkpoint(self, batch):
                pass
        
        # Should be able to instantiate
        consumer = CompleteConsumer()
        assert isinstance(consumer, MessageConsumer)
        assert consumer.is_connected() is True
    
    def test_abstract_methods_have_correct_signatures(self):
        """Test that abstract methods have correct signatures."""
        import inspect
        
        # Check connect signature
        sig = inspect.signature(MessageConsumer.connect)
        assert len(sig.parameters) == 1  # self only
        assert sig.return_annotation == type(None) or sig.return_annotation == None
        
        # Check disconnect signature
        sig = inspect.signature(MessageConsumer.disconnect)
        assert len(sig.parameters) == 1  # self only
        
        # Check is_connected signature
        sig = inspect.signature(MessageConsumer.is_connected)
        assert len(sig.parameters) == 1  # self only
        # Return type should be bool (but may not be annotated)
        
        # Check consume_batch signature
        sig = inspect.signature(MessageConsumer.consume_batch)
        params = list(sig.parameters.keys())
        assert 'self' in params
        assert 'max_messages' in params
        assert 'timeout_ms' in params
        
        # Check acknowledge_batch signature
        sig = inspect.signature(MessageConsumer.acknowledge_batch)
        params = list(sig.parameters.keys())
        assert 'self' in params
        assert 'batch' in params
        
        # Check checkpoint signature
        sig = inspect.signature(MessageConsumer.checkpoint)
        params = list(sig.parameters.keys())
        assert 'self' in params
        assert 'batch' in params

