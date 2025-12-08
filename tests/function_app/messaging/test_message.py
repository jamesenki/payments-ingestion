"""
Unit tests for Message and MessageBatch data structures.

Tests WO-29: Message and MessageBatch Data Structures
"""

import pytest
import json
from datetime import datetime
from src.function_app.messaging import Message, MessageBatch


class TestMessage:
    """Tests for Message dataclass."""
    
    def test_message_creation(self):
        """Test basic message creation with all fields."""
        msg = Message(
            message_id="msg-123",
            correlation_id="corr-456",
            timestamp=datetime.utcnow(),
            headers={"source": "test", "version": "1.0"},
            body='{"amount": 100.0}',
            offset=12345,
            sequence_number=67890
        )
        
        assert msg.message_id == "msg-123"
        assert msg.correlation_id == "corr-456"
        assert isinstance(msg.timestamp, datetime)
        assert msg.headers == {"source": "test", "version": "1.0"}
        assert msg.body == '{"amount": 100.0}'
        assert msg.offset == 12345
        assert msg.sequence_number == 67890
    
    def test_message_creation_with_defaults(self):
        """Test message creation with default values."""
        msg = Message(
            message_id="msg-1",
            correlation_id="corr-1",
            timestamp=datetime.utcnow()
        )
        
        assert msg.message_id == "msg-1"
        assert msg.correlation_id == "corr-1"
        assert msg.headers == {}
        assert msg.body == ""
        assert msg.offset == 0
        assert msg.sequence_number == 0
    
    def test_message_immutability(self):
        """Test that Message is immutable (frozen dataclass)."""
        msg = Message(
            message_id="msg-1",
            correlation_id="corr-1",
            timestamp=datetime.utcnow()
        )
        
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            msg.message_id = "new-id"
    
    def test_get_body_as_dict_valid_json(self, sample_message):
        """Test parsing valid JSON body."""
        data = sample_message.get_body_as_dict()
        
        assert isinstance(data, dict)
        assert data["amount"] == 100.0
        assert data["currency"] == "USD"
    
    def test_get_body_as_dict_invalid_json(self, sample_invalid_json_message):
        """Test handling invalid JSON gracefully."""
        data = sample_invalid_json_message.get_body_as_dict()
        
        # Should return empty dict, not raise exception
        assert isinstance(data, dict)
        assert data == {}
    
    def test_get_body_as_dict_empty_body(self, sample_empty_message):
        """Test handling empty body."""
        data = sample_empty_message.get_body_as_dict()
        
        assert isinstance(data, dict)
        assert data == {}
    
    def test_get_body_as_dict_complex_json(self):
        """Test parsing complex JSON structure."""
        complex_body = json.dumps({
            "transaction": {
                "id": "tx-123",
                "amount": 100.0,
                "items": [{"name": "item1", "price": 50.0}]
            },
            "metadata": {"source": "web"}
        })
        
        msg = Message(
            message_id="msg-1",
            correlation_id="corr-1",
            timestamp=datetime.utcnow(),
            body=complex_body
        )
        
        data = msg.get_body_as_dict()
        assert data["transaction"]["id"] == "tx-123"
        assert len(data["transaction"]["items"]) == 1
        assert data["metadata"]["source"] == "web"
    
    def test_get_body_as_dict_non_json_string(self):
        """Test handling non-JSON string body."""
        msg = Message(
            message_id="msg-1",
            correlation_id="corr-1",
            timestamp=datetime.utcnow(),
            body="just a plain string"
        )
        
        data = msg.get_body_as_dict()
        assert data == {}
    
    def test_get_body_as_dict_malformed_json(self):
        """Test handling malformed JSON (missing closing brace)."""
        msg = Message(
            message_id="msg-1",
            correlation_id="corr-1",
            timestamp=datetime.utcnow(),
            body='{"amount": 100.0, "currency": "USD"'
        )
        
        data = msg.get_body_as_dict()
        assert data == {}


class TestMessageBatch:
    """Tests for MessageBatch dataclass."""
    
    def test_batch_creation(self, sample_message_batch):
        """Test basic batch creation."""
        assert len(sample_message_batch.messages) == 2
        assert sample_message_batch.batch_id == "batch-123"
        assert isinstance(sample_message_batch.received_at, datetime)
        assert sample_message_batch.broker_type == "event_hubs"
    
    def test_batch_creation_with_defaults(self):
        """Test batch creation with default broker_type."""
        messages = [
            Message(
                message_id="msg-1",
                correlation_id="corr-1",
                timestamp=datetime.utcnow()
            )
        ]
        batch = MessageBatch(
            messages=messages,
            batch_id="batch-1",
            received_at=datetime.utcnow()
        )
        
        assert batch.broker_type == "event_hubs"  # Default
    
    def test_batch_len(self, sample_message_batch):
        """Test __len__ method."""
        assert len(sample_message_batch) == 2
    
    def test_batch_iteration(self, sample_message_batch):
        """Test __iter__ method for iteration."""
        messages = list(sample_message_batch)
        assert len(messages) == 2
        assert all(isinstance(msg, Message) for msg in messages)
    
    def test_batch_for_loop(self, sample_message_batch):
        """Test using batch in for loop."""
        count = 0
        for msg in sample_message_batch:
            assert isinstance(msg, Message)
            count += 1
        assert count == 2
    
    def test_batch_is_empty_false(self, sample_message_batch):
        """Test is_empty() returns False for non-empty batch."""
        assert sample_message_batch.is_empty() is False
    
    def test_batch_is_empty_true(self):
        """Test is_empty() returns True for empty batch."""
        batch = MessageBatch(
            messages=[],
            batch_id="batch-empty",
            received_at=datetime.utcnow()
        )
        assert batch.is_empty() is True
    
    def test_batch_get_first_message(self, sample_message_batch):
        """Test get_first_message() returns first message."""
        first = sample_message_batch.get_first_message()
        assert first is not None
        assert first.message_id == "msg-123"
    
    def test_batch_get_first_message_empty(self):
        """Test get_first_message() returns None for empty batch."""
        batch = MessageBatch(
            messages=[],
            batch_id="batch-empty",
            received_at=datetime.utcnow()
        )
        assert batch.get_first_message() is None
    
    def test_batch_get_last_message(self, sample_message_batch):
        """Test get_last_message() returns last message."""
        last = sample_message_batch.get_last_message()
        assert last is not None
        assert last.message_id == "msg-124"
    
    def test_batch_get_last_message_empty(self):
        """Test get_last_message() returns None for empty batch."""
        batch = MessageBatch(
            messages=[],
            batch_id="batch-empty",
            received_at=datetime.utcnow()
        )
        assert batch.get_last_message() is None
    
    def test_batch_get_first_and_last_same(self):
        """Test get_first_message() and get_last_message() for single message."""
        msg = Message(
            message_id="msg-1",
            correlation_id="corr-1",
            timestamp=datetime.utcnow()
        )
        batch = MessageBatch(
            messages=[msg],
            batch_id="batch-1",
            received_at=datetime.utcnow()
        )
        
        assert batch.get_first_message() == msg
        assert batch.get_last_message() == msg
        assert batch.get_first_message() == batch.get_last_message()
    
    def test_batch_immutability(self, sample_message_batch):
        """Test that MessageBatch is immutable (frozen dataclass)."""
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            sample_message_batch.batch_id = "new-id"
    
    def test_batch_with_kafka_broker(self):
        """Test batch with kafka broker type."""
        messages = [
            Message(
                message_id="msg-1",
                correlation_id="corr-1",
                timestamp=datetime.utcnow()
            )
        ]
        batch = MessageBatch(
            messages=messages,
            batch_id="batch-kafka",
            received_at=datetime.utcnow(),
            broker_type="kafka"
        )
        
        assert batch.broker_type == "kafka"

