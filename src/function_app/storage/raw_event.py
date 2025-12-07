"""
Raw Event data model for Parquet storage.

Implements WO-63: Raw Events Parquet Data Model and Serialization
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
import json


@dataclass(frozen=True)
class RawEvent:
    """
    Raw event data model for storing transaction payloads.
    
    This model represents a complete transaction event that will be stored
    in Azure Blob Storage as Parquet files for archival and compliance.
    
    Attributes:
        transaction_id: Unique identifier for the transaction
        correlation_id: Correlation ID for request tracing
        event_payload: Complete transaction data as dictionary
        created_at: Timestamp when the event was created
    """
    
    transaction_id: str
    correlation_id: UUID
    event_payload: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate RawEvent data after initialization."""
        if not self.transaction_id:
            raise ValueError("transaction_id cannot be empty")
        
        if not isinstance(self.correlation_id, UUID):
            raise ValueError("correlation_id must be a UUID")
        
        if not isinstance(self.event_payload, dict):
            raise ValueError("event_payload must be a dictionary")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert RawEvent to dictionary for serialization.
        
        Returns:
            Dictionary representation of the RawEvent
        """
        return {
            'transaction_id': self.transaction_id,
            'correlation_id': str(self.correlation_id),
            'event_payload': self.event_payload,
            'created_at': self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RawEvent':
        """
        Create RawEvent from dictionary.
        
        Args:
            data: Dictionary containing RawEvent fields
            
        Returns:
            RawEvent instance
        """
        # Handle correlation_id conversion
        correlation_id = data.get('correlation_id')
        if isinstance(correlation_id, str):
            correlation_id = UUID(correlation_id)
        elif not isinstance(correlation_id, UUID):
            raise ValueError("correlation_id must be UUID or UUID string")
        
        # Handle created_at conversion
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif not isinstance(created_at, datetime):
            created_at = datetime.utcnow()
        
        return cls(
            transaction_id=data['transaction_id'],
            correlation_id=correlation_id,
            event_payload=data.get('event_payload', {}),
            created_at=created_at,
        )
    
    def get_event_payload_json(self) -> str:
        """
        Get event_payload as JSON string for Parquet storage.
        
        Returns:
            JSON-encoded string of event_payload
        """
        return json.dumps(self.event_payload, default=str)


class BufferError(Exception):
    """
    Exception raised for buffer-related errors in blob storage operations.
    
    This exception is raised when:
    - Buffer overflow occurs
    - Buffer serialization fails
    - Buffer flush operations fail
    """
    pass


class StorageError(Exception):
    """
    Exception raised for storage-related errors in blob storage operations.
    
    This exception is raised when:
    - Blob storage connection fails
    - File upload operations fail
    - Storage permissions are insufficient
    - Storage quota is exceeded
    """
    pass

