"""
Unit tests for RawEvent data model.

Tests WO-63: Raw Events Parquet Data Model and Serialization
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from uuid import UUID, uuid4

# Import raw_event directly to avoid importing blob_raw_event_store which requires Azure SDK
raw_event_path = Path(__file__).parent.parent.parent.parent / "src" / "function_app" / "storage" / "raw_event.py"
import importlib.util
spec = importlib.util.spec_from_file_location("raw_event", raw_event_path)
raw_event_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(raw_event_module)
RawEvent = raw_event_module.RawEvent
BufferError = raw_event_module.BufferError
StorageError = raw_event_module.StorageError


class TestRawEvent:
    """Tests for RawEvent dataclass."""
    
    def test_raw_event_creation(self):
        """Test basic RawEvent creation."""
        correlation_id = uuid4()
        event = RawEvent(
            transaction_id="tx-123",
            correlation_id=correlation_id,
            event_payload={"amount": 100.0, "currency": "USD"}
        )
        
        assert event.transaction_id == "tx-123"
        assert event.correlation_id == correlation_id
        assert event.event_payload == {"amount": 100.0, "currency": "USD"}
        assert isinstance(event.created_at, datetime)
    
    def test_raw_event_with_custom_timestamp(self):
        """Test RawEvent with custom created_at timestamp."""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        event = RawEvent(
            transaction_id="tx-1",
            correlation_id=uuid4(),
            event_payload={},
            created_at=timestamp
        )
        
        assert event.created_at == timestamp
    
    def test_raw_event_immutability(self):
        """Test that RawEvent is immutable (frozen dataclass)."""
        event = RawEvent(
            transaction_id="tx-1",
            correlation_id=uuid4(),
            event_payload={}
        )
        
        with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
            event.transaction_id = "new-id"
    
    def test_raw_event_validation_empty_transaction_id(self):
        """Test validation fails for empty transaction_id."""
        with pytest.raises(ValueError, match="transaction_id cannot be empty"):
            RawEvent(
                transaction_id="",
                correlation_id=uuid4(),
                event_payload={}
            )
    
    def test_raw_event_validation_invalid_correlation_id(self):
        """Test validation fails for invalid correlation_id."""
        with pytest.raises(ValueError, match="correlation_id must be a UUID"):
            RawEvent(
                transaction_id="tx-1",
                correlation_id="not-a-uuid",  # type: ignore
                event_payload={}
            )
    
    def test_raw_event_validation_invalid_payload(self):
        """Test validation fails for non-dict event_payload."""
        with pytest.raises(ValueError, match="event_payload must be a dictionary"):
            RawEvent(
                transaction_id="tx-1",
                correlation_id=uuid4(),
                event_payload="not-a-dict"  # type: ignore
            )
    
    def test_raw_event_to_dict(self):
        """Test to_dict() method."""
        correlation_id = uuid4()
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        event = RawEvent(
            transaction_id="tx-123",
            correlation_id=correlation_id,
            event_payload={"amount": 100.0, "currency": "USD"},
            created_at=timestamp
        )
        
        data = event.to_dict()
        
        assert data["transaction_id"] == "tx-123"
        assert data["correlation_id"] == str(correlation_id)
        assert data["event_payload"] == {"amount": 100.0, "currency": "USD"}
        assert data["created_at"] == "2025-01-01T12:00:00"
    
    def test_raw_event_from_dict(self):
        """Test from_dict() class method."""
        correlation_id = uuid4()
        data = {
            "transaction_id": "tx-123",
            "correlation_id": str(correlation_id),
            "event_payload": {"amount": 100.0},
            "created_at": "2025-01-01T12:00:00"
        }
        
        event = RawEvent.from_dict(data)
        
        assert event.transaction_id == "tx-123"
        assert event.correlation_id == correlation_id
        assert event.event_payload == {"amount": 100.0}
        assert event.created_at == datetime(2025, 1, 1, 12, 0, 0)
    
    def test_raw_event_from_dict_with_uuid_object(self):
        """Test from_dict() with UUID object instead of string."""
        correlation_id = uuid4()
        data = {
            "transaction_id": "tx-123",
            "correlation_id": correlation_id,  # UUID object
            "event_payload": {},
            "created_at": datetime(2025, 1, 1, 12, 0, 0)
        }
        
        event = RawEvent.from_dict(data)
        assert event.correlation_id == correlation_id
    
    def test_raw_event_from_dict_with_datetime_object(self):
        """Test from_dict() with datetime object instead of string."""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        data = {
            "transaction_id": "tx-123",
            "correlation_id": str(uuid4()),
            "event_payload": {},
            "created_at": timestamp  # datetime object
        }
        
        event = RawEvent.from_dict(data)
        assert event.created_at == timestamp
    
    def test_raw_event_from_dict_with_iso_string(self):
        """Test from_dict() with ISO format string with Z."""
        data = {
            "transaction_id": "tx-123",
            "correlation_id": str(uuid4()),
            "event_payload": {},
            "created_at": "2025-01-01T12:00:00Z"
        }
        
        event = RawEvent.from_dict(data)
        assert isinstance(event.created_at, datetime)
    
    def test_raw_event_from_dict_missing_created_at(self):
        """Test from_dict() defaults created_at when missing."""
        data = {
            "transaction_id": "tx-123",
            "correlation_id": str(uuid4()),
            "event_payload": {}
        }
        
        event = RawEvent.from_dict(data)
        assert isinstance(event.created_at, datetime)
    
    def test_raw_event_from_dict_invalid_correlation_id(self):
        """Test from_dict() raises error for invalid correlation_id."""
        data = {
            "transaction_id": "tx-123",
            "correlation_id": "not-a-uuid",
            "event_payload": {}
        }
        
        # UUID() raises ValueError when given invalid string, which gets caught
        # and re-raised with our message, or the original ValueError is raised
        with pytest.raises(ValueError):
            RawEvent.from_dict(data)
    
    def test_raw_event_get_event_payload_json(self):
        """Test get_event_payload_json() method."""
        event = RawEvent(
            transaction_id="tx-123",
            correlation_id=uuid4(),
            event_payload={"amount": 100.0, "currency": "USD", "nested": {"key": "value"}}
        )
        
        json_str = event.get_event_payload_json()
        assert isinstance(json_str, str)
        # Verify it's valid JSON
        import json
        parsed = json.loads(json_str)
        assert parsed["amount"] == 100.0
        assert parsed["currency"] == "USD"
        assert parsed["nested"]["key"] == "value"
    
    def test_raw_event_get_event_payload_json_complex(self):
        """Test get_event_payload_json() with complex nested data."""
        event = RawEvent(
            transaction_id="tx-123",
            correlation_id=uuid4(),
            event_payload={
                "amount": 100.0,
                "items": [{"name": "item1", "price": 50.0}, {"name": "item2", "price": 50.0}],
                "metadata": {"source": "web", "device": "mobile"}
            }
        )
        
        json_str = event.get_event_payload_json()
        import json
        parsed = json.loads(json_str)
        assert len(parsed["items"]) == 2
        assert parsed["metadata"]["source"] == "web"


class TestRawEventExceptions:
    """Tests for RawEvent custom exceptions."""
    
    def test_buffer_error(self):
        """Test BufferError exception."""
        error = BufferError("Buffer overflow")
        assert isinstance(error, Exception)
        assert str(error) == "Buffer overflow"
    
    def test_storage_error(self):
        """Test StorageError exception."""
        error = StorageError("Storage connection failed")
        assert isinstance(error, Exception)
        assert str(error) == "Storage connection failed"
    
    def test_buffer_error_inheritance(self):
        """Test BufferError inheritance."""
        assert issubclass(BufferError, Exception)
    
    def test_storage_error_inheritance(self):
        """Test StorageError inheritance."""
        assert issubclass(StorageError, Exception)

