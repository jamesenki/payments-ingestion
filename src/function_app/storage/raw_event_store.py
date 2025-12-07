"""
Raw Event Store interface and implementations.

Defines the interface for storing raw events to various backends.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from .raw_event import RawEvent


class RawEventStore(ABC):
    """
    Abstract base class for raw event storage implementations.
    
    This interface allows for different storage backends (Blob Storage, PostgreSQL, etc.)
    while maintaining a consistent API.
    """
    
    @abstractmethod
    def store_event(self, event: RawEvent) -> Optional[str]:
        """
        Store a single raw event.
        
        Args:
            event: RawEvent to store
            
        Returns:
            Storage identifier (e.g., blob path, database ID) or None if buffered
        """
        pass
    
    @abstractmethod
    def store_events_batch(self, events: List[RawEvent]) -> List[str]:
        """
        Store multiple raw events in a batch.
        
        Args:
            events: List of RawEvent objects to store
            
        Returns:
            List of storage identifiers
        """
        pass
    
    @abstractmethod
    def flush(self) -> int:
        """
        Flush any buffered events to storage.
        
        Returns:
            Number of events flushed
        """
        pass
    
    @abstractmethod
    def close(self):
        """Close the store and flush any remaining events."""
        pass

