"""
Message and MessageBatch data structures.

Implements WO-29: Message and MessageBatch Data Structures

This module provides the foundational data structures for representing
messages and message batches from Event Hubs/Kafka, enabling consistent
message handling across different broker implementations.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Iterator, Optional


@dataclass(frozen=True)
class Message:
    """
    Represents a single message from a message broker (Event Hubs or Kafka).
    
    This dataclass provides an immutable representation of a message with
    all necessary metadata for processing, tracking, and error handling.
    
    Attributes:
        message_id: Unique identifier for the message
        correlation_id: Correlation ID for request tracing across services
        timestamp: Timestamp when the message was created/published
        headers: Dictionary of message headers (metadata)
        body: Raw message body as string (typically JSON)
        offset: Message offset in the partition (for Kafka/Event Hubs)
        sequence_number: Sequence number of the message (for Event Hubs)
    
    Example:
        >>> msg = Message(
        ...     message_id="msg-123",
        ...     correlation_id="corr-456",
        ...     timestamp=datetime.utcnow(),
        ...     headers={"source": "payment-gateway"},
        ...     body='{"amount": 100.0, "currency": "USD"}',
        ...     offset=12345,
        ...     sequence_number=67890
        ... )
        >>> data = msg.get_body_as_dict()
        >>> print(data["amount"])
        100.0
    """
    
    message_id: str
    correlation_id: str
    timestamp: datetime
    headers: Dict[str, str] = field(default_factory=dict)
    body: str = ""
    offset: int = 0
    sequence_number: int = 0
    
    def get_body_as_dict(self) -> Dict[str, Any]:
        """
        Parse the message body as JSON and return as dictionary.
        
        This method handles JSON parsing errors gracefully by returning
        an empty dictionary if parsing fails, rather than raising an exception.
        This allows the message to be processed even if the body format is
        unexpected or corrupted.
        
        Returns:
            Dictionary representation of the message body, or empty dict if
            parsing fails
            
        Example:
            >>> msg = Message(
            ...     message_id="msg-1",
            ...     correlation_id="corr-1",
            ...     timestamp=datetime.utcnow(),
            ...     body='{"amount": 100.0, "currency": "USD"}'
            ... )
            >>> data = msg.get_body_as_dict()
            >>> data["amount"]
            100.0
        """
        if not self.body:
            return {}
        
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:
            # Return empty dict on JSON parsing errors
            # This allows processing to continue with other message fields
            return {}
        except Exception:
            # Handle any other unexpected errors gracefully
            return {}


@dataclass(frozen=True)
class MessageBatch:
    """
    Represents a batch of messages from a message broker.
    
    This dataclass provides a container for multiple messages that were
    received together, along with batch-level metadata. It supports
    iteration and length operations for convenient processing.
    
    Attributes:
        messages: List of Message objects in the batch
        batch_id: Unique identifier for this batch
        received_at: Timestamp when the batch was received
        broker_type: Type of broker ("event_hubs" or "kafka")
    
    Example:
        >>> batch = MessageBatch(
        ...     messages=[msg1, msg2, msg3],
        ...     batch_id="batch-123",
        ...     received_at=datetime.utcnow(),
        ...     broker_type="event_hubs"
        ... )
        >>> len(batch)
        3
        >>> for msg in batch:
        ...     process(msg)
    """
    
    messages: List[Message]
    batch_id: str
    received_at: datetime
    broker_type: str = "event_hubs"
    
    def __len__(self) -> int:
        """
        Return the count of messages in the batch.
        
        This enables the use of len() function on MessageBatch instances,
        making it easy to check batch size and iterate over messages.
        
        Returns:
            Number of messages in the batch
            
        Example:
            >>> batch = MessageBatch(messages=[msg1, msg2], ...)
            >>> len(batch)
            2
        """
        return len(self.messages)
    
    def __iter__(self) -> Iterator[Message]:
        """
        Enable iteration over messages in the batch.
        
        This allows MessageBatch to be used directly in for loops and
        other iteration contexts, making message processing more intuitive.
        
        Yields:
            Message objects from the batch, one at a time
            
        Example:
            >>> batch = MessageBatch(messages=[msg1, msg2, msg3], ...)
            >>> for message in batch:
            ...     process_message(message)
        """
        return iter(self.messages)
    
    def is_empty(self) -> bool:
        """
        Check if the batch contains any messages.
        
        Returns:
            True if batch is empty, False otherwise
        """
        return len(self.messages) == 0
    
    def get_first_message(self) -> Optional[Message]:
        """
        Get the first message in the batch, if any.
        
        Returns:
            First Message in the batch, or None if batch is empty
        """
        return self.messages[0] if self.messages else None
    
    def get_last_message(self) -> Optional[Message]:
        """
        Get the last message in the batch, if any.
        
        Returns:
            Last Message in the batch, or None if batch is empty
        """
        return self.messages[-1] if self.messages else None

