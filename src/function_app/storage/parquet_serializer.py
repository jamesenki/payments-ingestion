"""
Parquet serialization for raw events.

Implements WO-63: Raw Events Parquet Data Model and Serialization
"""

from typing import List, Optional, Any
from datetime import datetime
from uuid import UUID
import pyarrow as pa
import pyarrow.parquet as pq
import json
from decimal import Decimal

from .raw_event import RawEvent, BufferError, StorageError


# Parquet schema definition based on NormalizedTransactions structure
# See: docs/PARQUET-SCHEMA-DESIGN.md
PARQUET_SCHEMA = pa.schema([
    # Primary Identifier
    pa.field('transaction_id', pa.string()),
    pa.field('correlation_id', pa.string()),  # UUID as string
    
    # Temporal Information
    pa.field('transaction_timestamp', pa.timestamp('ns', tz='UTC')),
    pa.field('ingestion_timestamp', pa.timestamp('ns', tz='UTC', nullable=True)),
    pa.field('processing_timestamp', pa.timestamp('ns', tz='UTC', nullable=True)),
    
    # Transaction Details
    pa.field('amount', pa.decimal128(19, 4)),
    pa.field('currency', pa.string()),
    pa.field('payment_method', pa.string()),
    pa.field('payment_status', pa.string()),
    
    # Customer Information (nullable)
    pa.field('customer_id', pa.string(), nullable=True),
    pa.field('customer_email', pa.string(), nullable=True),
    pa.field('customer_country', pa.string(), nullable=True),
    
    # Merchant Information (nullable)
    pa.field('merchant_id', pa.string(), nullable=True),
    pa.field('merchant_name', pa.string(), nullable=True),
    pa.field('merchant_category', pa.string(), nullable=True),
    
    # Transaction Metadata (nullable)
    pa.field('transaction_type', pa.string(), nullable=True),
    pa.field('channel', pa.string(), nullable=True),
    pa.field('device_type', pa.string(), nullable=True),
    
    # Additional Data (JSON stored as string)
    pa.field('metadata', pa.string(), nullable=True),  # JSON-encoded
    
    # Audit Fields
    pa.field('created_at', pa.timestamp('ns', tz='UTC')),
    pa.field('updated_at', pa.timestamp('ns', tz='UTC', nullable=True)),
])


class ParquetSerializer:
    """
    Serializes RawEvent objects to Parquet format.
    
    This class handles conversion of RawEvent objects to PyArrow Table format
    and serialization to compressed Parquet bytes for efficient storage.
    """
    
    def __init__(self, compression: str = 'snappy'):
        """
        Initialize ParquetSerializer.
        
        Args:
            compression: Compression algorithm ('snappy', 'gzip', 'brotli', 'zstd', 'lz4', 'none')
        """
        self.compression = compression
        self.schema = PARQUET_SCHEMA
    
    def _events_to_arrow_table(self, events: List[RawEvent]) -> pa.Table:
        """
        Convert List[RawEvent] objects to PyArrow Table format.
        
        This method extracts transaction data from RawEvent.event_payload
        and maps it to the Parquet schema with proper data type conversion.
        
        Args:
            events: List of RawEvent objects to convert
            
        Returns:
            PyArrow Table with schema matching PARQUET_SCHEMA
            
        Raises:
            BufferError: If conversion fails due to invalid data
        """
        if not events:
            raise BufferError("Cannot convert empty event list to Arrow table")
        
        try:
            # Extract data from RawEvent objects
            data = []
            for event in events:
                payload = event.event_payload
                
                # Extract transaction data from payload
                row = {
                    'transaction_id': event.transaction_id,
                    'correlation_id': str(event.correlation_id),
                    'transaction_timestamp': self._parse_timestamp(
                        payload.get('transaction_timestamp', event.created_at)
                    ),
                    'ingestion_timestamp': self._parse_timestamp(
                        payload.get('ingestion_timestamp')
                    ),
                    'processing_timestamp': self._parse_timestamp(
                        payload.get('processing_timestamp')
                    ),
                    'amount': self._parse_decimal(payload.get('amount')),
                    'currency': payload.get('currency', ''),
                    'payment_method': payload.get('payment_method', ''),
                    'payment_status': payload.get('payment_status', ''),
                    'customer_id': payload.get('customer_id'),
                    'customer_email': payload.get('customer_email'),
                    'customer_country': payload.get('customer_country'),
                    'merchant_id': payload.get('merchant_id'),
                    'merchant_name': payload.get('merchant_name'),
                    'merchant_category': payload.get('merchant_category'),
                    'transaction_type': payload.get('transaction_type'),
                    'channel': payload.get('channel'),
                    'device_type': payload.get('device_type'),
                    'metadata': json.dumps(payload.get('metadata', {}), default=str) if payload.get('metadata') else None,
                    'created_at': event.created_at,
                    'updated_at': self._parse_timestamp(payload.get('updated_at')),
                }
                data.append(row)
            
            # Convert to PyArrow Table
            table = pa.Table.from_pylist(data, schema=self.schema)
            
            return table
            
        except Exception as e:
            raise BufferError(f"Failed to convert events to Arrow table: {str(e)}") from e
    
    def _parse_timestamp(self, value: Optional[Any]) -> Optional[datetime]:
        """
        Parse timestamp value to datetime.
        
        Args:
            value: Timestamp value (datetime, string, or None)
            
        Returns:
            datetime object or None
        """
        if value is None:
            return None
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                # Try other formats if needed
                pass
        
        return None
    
    def _parse_decimal(self, value: Optional[Any]) -> Decimal:
        """
        Parse decimal value.
        
        Args:
            value: Decimal value (Decimal, float, int, string, or None)
            
        Returns:
            Decimal object
        """
        if value is None:
            return Decimal('0')
        
        if isinstance(value, Decimal):
            return value
        
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        
        if isinstance(value, str):
            return Decimal(value)
        
        return Decimal('0')
    
    def _serialize_to_parquet(self, table: pa.Table) -> bytes:
        """
        Convert PyArrow Table to compressed Parquet bytes.
        
        This method serializes the Arrow table to Parquet format with
        compression for efficient storage.
        
        Args:
            table: PyArrow Table to serialize
            
        Returns:
            Compressed Parquet bytes
            
        Raises:
            BufferError: If serialization fails
        """
        try:
            # Use BytesIO to write to memory
            import io
            buffer = io.BytesIO()
            
            # Write table to Parquet format
            pq.write_table(
                table,
                buffer,
                compression=self.compression,
                use_dictionary=True,  # Enable dictionary encoding for better compression
                write_statistics=True,  # Include statistics for query optimization
            )
            
            # Get bytes from buffer
            buffer.seek(0)
            parquet_bytes = buffer.read()
            
            return parquet_bytes
            
        except Exception as e:
            raise BufferError(f"Failed to serialize to Parquet: {str(e)}") from e
    
    def serialize_events(self, events: List[RawEvent]) -> bytes:
        """
        Serialize list of RawEvent objects to Parquet bytes.
        
        This is the main public method that orchestrates the conversion
        and serialization process.
        
        Args:
            events: List of RawEvent objects to serialize
            
        Returns:
            Compressed Parquet bytes
            
        Raises:
            BufferError: If serialization fails
        """
        if not events:
            raise BufferError("Cannot serialize empty event list")
        
        # Convert to Arrow table
        table = self._events_to_arrow_table(events)
        
        # Serialize to Parquet
        parquet_bytes = self._serialize_to_parquet(table)
        
        return parquet_bytes
    
    def deserialize_events(self, parquet_bytes: bytes) -> List[RawEvent]:
        """
        Deserialize Parquet bytes back to RawEvent objects.
        
        This method supports round-trip conversion from Parquet to RawEvent,
        ensuring no data loss during serialization/deserialization.
        
        Args:
            parquet_bytes: Compressed Parquet bytes
            
        Returns:
            List of RawEvent objects
            
        Raises:
            StorageError: If deserialization fails
        """
        try:
            import io
            
            # Read Parquet from bytes
            buffer = io.BytesIO(parquet_bytes)
            table = pq.read_table(buffer)
            
            # Convert to list of dictionaries
            data = table.to_pylist()
            
            # Convert to RawEvent objects
            events = []
            for row in data:
                # Reconstruct event_payload from row data
                event_payload = {
                    'transaction_timestamp': row.get('transaction_timestamp'),
                    'ingestion_timestamp': row.get('ingestion_timestamp'),
                    'processing_timestamp': row.get('processing_timestamp'),
                    'amount': float(row.get('amount', 0)) if row.get('amount') else 0,
                    'currency': row.get('currency'),
                    'payment_method': row.get('payment_method'),
                    'payment_status': row.get('payment_status'),
                    'customer_id': row.get('customer_id'),
                    'customer_email': row.get('customer_email'),
                    'customer_country': row.get('customer_country'),
                    'merchant_id': row.get('merchant_id'),
                    'merchant_name': row.get('merchant_name'),
                    'merchant_category': row.get('merchant_category'),
                    'transaction_type': row.get('transaction_type'),
                    'channel': row.get('channel'),
                    'device_type': row.get('device_type'),
                    'updated_at': row.get('updated_at'),
                }
                
                # Parse metadata if present
                if row.get('metadata'):
                    try:
                        event_payload['metadata'] = json.loads(row['metadata'])
                    except json.JSONDecodeError:
                        event_payload['metadata'] = {}
                
                # Parse correlation_id
                correlation_id_str = row.get('correlation_id', '00000000-0000-0000-0000-000000000000')
                try:
                    correlation_id = UUID(correlation_id_str)
                except (ValueError, TypeError):
                    correlation_id = UUID('00000000-0000-0000-0000-000000000000')
                
                # Create RawEvent
                event = RawEvent(
                    transaction_id=row['transaction_id'],
                    correlation_id=correlation_id,
                    event_payload=event_payload,
                    created_at=row.get('created_at', datetime.utcnow()),
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            raise StorageError(f"Failed to deserialize Parquet bytes: {str(e)}") from e
    
    def validate_parquet_file(self, parquet_bytes: bytes) -> bool:
        """
        Validate that Parquet bytes are readable and schema-compatible.
        
        Args:
            parquet_bytes: Compressed Parquet bytes to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            import io
            
            buffer = io.BytesIO(parquet_bytes)
            table = pq.read_table(buffer)
            
            # Check schema compatibility
            # Allow additional fields but require core fields
            required_fields = ['transaction_id', 'created_at']
            schema_fields = [field.name for field in table.schema]
            
            for field in required_fields:
                if field not in schema_fields:
                    return False
            
            return True
            
        except Exception:
            return False

