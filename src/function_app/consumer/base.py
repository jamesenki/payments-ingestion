"""
MessageConsumer abstract base class and interface.

Implements WO-36: MessageConsumer Abstract Base Class and Interface

This module establishes the common interface and contract for all message
consumer implementations, providing a consistent API for consuming messages
regardless of the underlying broker (Event Hubs or Kafka).
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..messaging import MessageBatch


class MessageConsumer(ABC):
    """
    Abstract base class for message consumer implementations.
    
    This class defines the common interface that all message consumers must
    implement, regardless of the underlying broker type (Event Hubs or Kafka).
    This enables the adapter pattern architecture, allowing the system to
    work with different message brokers through a unified interface.
    
    Concrete implementations should inherit from this class and implement
    all abstract methods according to their specific broker requirements.
    
    Example:
        >>> class EventHubsConsumer(MessageConsumer):
        ...     def connect(self):
        ...         # Event Hubs connection logic
        ...         pass
        ...     
        ...     def consume_batch(self, max_messages=100, timeout_ms=1000):
        ...         # Event Hubs batch consumption logic
        ...         pass
        ...     
        ...     # ... implement other abstract methods
    """
    
    @abstractmethod
    def connect(self) -> None:
        """
        Establish connection to the message broker.
        
        This method should initialize the connection to the underlying
        message broker (Event Hubs or Kafka) and prepare it for message
        consumption. It should handle connection errors and raise appropriate
        exceptions if the connection cannot be established.
        
        Raises:
            ConnectionError: If connection to broker fails
            ValueError: If connection parameters are invalid
            
        Example:
            >>> consumer = EventHubsConsumer(...)
            >>> consumer.connect()
            >>> assert consumer.is_connected()
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close connection to the message broker.
        
        This method should gracefully close the connection to the underlying
        message broker, ensuring that any in-flight operations are completed
        or properly cancelled. It should be safe to call this method even
        if already disconnected.
        
        After calling this method, is_connected() should return False.
        
        Example:
            >>> consumer.connect()
            >>> consumer.disconnect()
            >>> assert not consumer.is_connected()
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if currently connected to the message broker.
        
        This method should return the current connection status. It should
        accurately reflect whether the consumer can successfully consume
        messages from the broker.
        
        Returns:
            True if connected and ready to consume messages, False otherwise
            
        Example:
            >>> consumer.connect()
            >>> if consumer.is_connected():
            ...     batch = consumer.consume_batch()
        """
        pass
    
    @abstractmethod
    def consume_batch(
        self,
        max_messages: int = 100,
        timeout_ms: int = 1000
    ) -> Optional[MessageBatch]:
        """
        Consume a batch of messages from the broker.
        
        This method should retrieve messages from the broker and return
        them as a MessageBatch. It should respect the max_messages limit
        and timeout_ms timeout. If no messages are available within the
        timeout, it should return None.
        
        Args:
            max_messages: Maximum number of messages to retrieve in this batch
            timeout_ms: Maximum time to wait for messages in milliseconds
        
        Returns:
            MessageBatch containing messages, or None if no messages available
            within the timeout period
            
        Raises:
            ConnectionError: If not connected to broker
            TimeoutError: If operation times out (optional, may return None)
            
        Example:
            >>> consumer.connect()
            >>> batch = consumer.consume_batch(max_messages=50, timeout_ms=2000)
            >>> if batch:
            ...     for message in batch:
            ...         process(message)
        """
        pass
    
    @abstractmethod
    def acknowledge_batch(self, batch: MessageBatch) -> None:
        """
        Acknowledge that a batch of messages has been successfully processed.
        
        This method should inform the broker that the messages in the batch
        have been successfully processed and can be removed from the broker's
        queue. The exact semantics depend on the broker type:
        - Event Hubs: Updates checkpoint
        - Kafka: Commits offsets
        
        Args:
            batch: MessageBatch that was successfully processed
            
        Raises:
            ConnectionError: If not connected to broker
            ValueError: If batch is invalid or empty
            
        Example:
            >>> batch = consumer.consume_batch()
            >>> if batch:
            ...     process_batch(batch)
            ...     consumer.acknowledge_batch(batch)
        """
        pass
    
    @abstractmethod
    def checkpoint(self, batch: MessageBatch) -> None:
        """
        Create a recovery checkpoint for a batch of messages.
        
        This method should create a checkpoint that allows the consumer to
        resume processing from this point in case of failure. The checkpoint
        should be stored persistently and should enable exactly-once or
        at-least-once processing semantics depending on broker capabilities.
        
        Args:
            batch: MessageBatch to checkpoint
            
        Raises:
            ConnectionError: If not connected to broker
            ValueError: If batch is invalid or empty
            
        Example:
            >>> batch = consumer.consume_batch()
            >>> if batch:
            ...     process_batch(batch)
            ...     consumer.checkpoint(batch)  # Save progress
        """
        pass

