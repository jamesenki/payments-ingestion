"""
Unit tests for ParquetSerializer.

Tests WO-63: Raw Events Parquet Data Model and Serialization
"""

import pytest
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from uuid import uuid4
from decimal import Decimal
import io

# Import modules - storage/__init__.py now has conditional imports for Azure SDK
import sys
from pathlib import Path

storage_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(storage_path))

from src.function_app.storage.raw_event import RawEvent, BufferError
from src.function_app.storage.parquet_serializer import ParquetSerializer, PARQUET_SCHEMA


class TestParquetSerializer:
    """Tests for ParquetSerializer class."""
    
    def test_serializer_initialization_default(self):
        """Test ParquetSerializer initialization with default compression."""
        serializer = ParquetSerializer()
        assert serializer.compression == 'snappy'
        assert serializer.schema == PARQUET_SCHEMA
    
    def test_serializer_initialization_custom_compression(self):
        """Test ParquetSerializer initialization with custom compression."""
        serializer = ParquetSerializer(compression='gzip')
        assert serializer.compression == 'gzip'
    
    def test_serializer_initialization_all_compressions(self):
        """Test ParquetSerializer with different compression algorithms."""
        for compression in ['snappy', 'gzip', 'brotli', 'zstd', 'lz4', 'none']:
            serializer = ParquetSerializer(compression=compression)
            assert serializer.compression == compression
    
    def test_events_to_arrow_table_empty_list(self):
        """Test converting empty list of events raises BufferError."""
        serializer = ParquetSerializer()
        # Empty list should raise BufferError according to implementation
        with pytest.raises(BufferError):
            serializer._events_to_arrow_table([])
    
    def test_events_to_arrow_table_single_event(self):
        """Test converting single event to Arrow table."""
        serializer = ParquetSerializer()
        event = RawEvent(
            transaction_id="tx-123",
            correlation_id=uuid4(),
            event_payload={
                "amount": "100.50",
                "currency": "USD",
                "payment_method": "credit_card",
                "payment_status": "completed",
                "customer_id": "cust-1",
                "merchant_id": "merchant-1"
            }
        )
        
        table = serializer._events_to_arrow_table([event])
        
        assert isinstance(table, pa.Table)
        assert len(table) == 1
        assert table.schema == PARQUET_SCHEMA
        assert table['transaction_id'][0].as_py() == "tx-123"
    
    def test_events_to_arrow_table_multiple_events(self):
        """Test converting multiple events to Arrow table."""
        serializer = ParquetSerializer()
        events = [
            RawEvent(
                transaction_id=f"tx-{i}",
                correlation_id=uuid4(),
                event_payload={
                    "amount": str(100.0 + i),
                    "currency": "USD",
                    "payment_method": "credit_card"
                }
            )
            for i in range(5)
        ]
        
        table = serializer._events_to_arrow_table(events)
        
        assert isinstance(table, pa.Table)
        assert len(table) == 5
        assert all(table['transaction_id'][i].as_py() == f"tx-{i}" for i in range(5))
    
    def test_serialize_to_parquet_bytes_empty(self):
        """Test serializing empty list raises BufferError."""
        serializer = ParquetSerializer()
        events = []
        
        # Empty list should raise BufferError according to implementation
        with pytest.raises(BufferError):
            serializer.serialize_events(events)
    
    def test_serialize_to_parquet_bytes_single_event(self):
        """Test serializing single event to Parquet bytes."""
        serializer = ParquetSerializer()
        event = RawEvent(
            transaction_id="tx-123",
            correlation_id=uuid4(),
            event_payload={
                "amount": "100.50",
                "currency": "USD"
            }
        )
        
        parquet_bytes = serializer.serialize_events([event])
        
        assert isinstance(parquet_bytes, bytes)
        assert len(parquet_bytes) > 0
        
        # Verify it's valid Parquet by reading it back
        buffer = io.BytesIO(parquet_bytes)
        table = pq.read_table(buffer)
        assert len(table) == 1
        assert table['transaction_id'][0].as_py() == "tx-123"
    
    def test_serialize_to_parquet_bytes_multiple_events(self):
        """Test serializing multiple events to Parquet bytes."""
        serializer = ParquetSerializer()
        events = [
            RawEvent(
                transaction_id=f"tx-{i}",
                correlation_id=uuid4(),
                event_payload={"amount": str(100.0 + i)}
            )
            for i in range(10)
        ]
        
        parquet_bytes = serializer.serialize_events(events)
        
        assert isinstance(parquet_bytes, bytes)
        
        # Verify by reading back
        buffer = io.BytesIO(parquet_bytes)
        table = pq.read_table(buffer)
        assert len(table) == 10
    
    def test_serialize_to_parquet_bytes_different_compressions(self):
        """Test serializing with different compression algorithms."""
        event = RawEvent(
            transaction_id="tx-1",
            correlation_id=uuid4(),
            event_payload={"amount": "100.0"}
        )
        
        for compression in ['snappy', 'gzip', 'none']:
            serializer = ParquetSerializer(compression=compression)
            parquet_bytes = serializer.serialize_events([event])
            assert isinstance(parquet_bytes, bytes)
            assert len(parquet_bytes) > 0
    
    def test_serialize_to_parquet_bytes_with_nullable_fields(self):
        """Test serializing events with nullable fields."""
        serializer = ParquetSerializer()
        event = RawEvent(
            transaction_id="tx-123",
            correlation_id=uuid4(),
            event_payload={
                "amount": "100.50",
                "currency": "USD",
                # Missing optional fields (should be None/nullable)
            }
        )
        
        parquet_bytes = serializer.serialize_events([event])
        
        # Should not raise error even with missing optional fields
        assert isinstance(parquet_bytes, bytes)
        
        # Verify by reading back
        buffer = io.BytesIO(parquet_bytes)
        table = pq.read_table(buffer)
        assert len(table) == 1
        # Nullable fields should be None
        assert table['customer_id'][0].as_py() is None or table['customer_id'][0].as_py() == ""
    
    def test_serialize_to_parquet_bytes_with_metadata(self):
        """Test serializing events with metadata field."""
        serializer = ParquetSerializer()
        event = RawEvent(
            transaction_id="tx-123",
            correlation_id=uuid4(),
            event_payload={
                "amount": "100.50",
                "currency": "USD",
                "metadata": {"source": "web", "device": "mobile"}
            }
        )
        
        parquet_bytes = serializer.serialize_events([event])
        
        assert isinstance(parquet_bytes, bytes)
        
        # Verify metadata is stored as JSON string
        buffer = io.BytesIO(parquet_bytes)
        table = pq.read_table(buffer)
        metadata_str = table['metadata'][0].as_py()
        assert metadata_str is not None
        import json
        metadata = json.loads(metadata_str)
        assert metadata["source"] == "web"
    
    def test_serialize_to_parquet_bytes_large_batch(self):
        """Test serializing large batch of events."""
        serializer = ParquetSerializer()
        events = [
            RawEvent(
                transaction_id=f"tx-{i:05d}",
                correlation_id=uuid4(),
                event_payload={
                    "amount": str(100.0 + i),
                    "currency": "USD",
                    "payment_method": "credit_card" if i % 2 == 0 else "debit_card"
                }
            )
            for i in range(100)
        ]
        
        parquet_bytes = serializer.serialize_events(events)
        
        assert isinstance(parquet_bytes, bytes)
        
        # Verify by reading back
        buffer = io.BytesIO(parquet_bytes)
        table = pq.read_table(buffer)
        assert len(table) == 100
    
    def test_parquet_schema_structure(self):
        """Test that PARQUET_SCHEMA has expected structure."""
        assert isinstance(PARQUET_SCHEMA, pa.Schema)
        
        # Check key fields exist
        field_names = [field.name for field in PARQUET_SCHEMA]
        assert 'transaction_id' in field_names
        assert 'correlation_id' in field_names
        assert 'amount' in field_names
        assert 'currency' in field_names
        assert 'created_at' in field_names
    
    def test_parquet_schema_field_types(self):
        """Test that PARQUET_SCHEMA has correct field types."""
        transaction_id_field = PARQUET_SCHEMA.field('transaction_id')
        assert transaction_id_field.type == pa.string()
        
        amount_field = PARQUET_SCHEMA.field('amount')
        assert isinstance(amount_field.type, pa.Decimal128Type)
        
        created_at_field = PARQUET_SCHEMA.field('created_at')
        assert isinstance(created_at_field.type, pa.TimestampType)
        assert created_at_field.type.unit == 'ns'
        assert created_at_field.type.tz == 'UTC'

