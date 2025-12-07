"""
Apache Kafka consumer implementation.

Implements WO-52: KafkaConsumer with Connection Management and Batch Processing

This module provides a concrete implementation of MessageConsumer for Apache Kafka,
enabling the system to consume messages with proper connection management, batch
retrieval, offset acknowledgment, and checkpointing capabilities.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

from .base import MessageConsumer
from ..messaging import Message, MessageBatch

logger = logging.getLogger(__name__)


class KafkaConsumer(MessageConsumer):
    """
    Concrete implementation of MessageConsumer for Apache Kafka.
    
    This class provides a complete implementation for consuming messages from
    Apache Kafka with automatic reconnection, batch processing, consumer group
    coordination, and offset management.
    
    Features:
    - Connection management with automatic reconnection
    - Batch message retrieval with configurable size and timeout
    - Offset acknowledgment and checkpointing
    - Consumer group coordination for multiple instances
    - Exponential backoff retry logic
    """
    
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        consumer_group: str
    ):
        """
        Initialize KafkaConsumer.
        
        Args:
            bootstrap_servers: Comma-separated list of Kafka broker addresses
            topic: Kafka topic to consume from
            consumer_group: Consumer group ID for coordination
        """
        if not KAFKA_AVAILABLE:
            raise ImportError(
                "kafka-python package is required. "
                "Install with: pip install kafka-python"
            )
        
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer_group = consumer_group
        
        self._consumer: Optional[KafkaConsumer] = None
        self._connected = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._base_backoff_seconds = 2
        self._max_backoff_seconds = 30
        
        logger.info(
            f"KafkaConsumer initialized: topic={topic}, "
            f"consumer_group={consumer_group}, "
            f"bootstrap_servers={bootstrap_servers}"
        )
    
    def connect(self) -> None:
        """
        Establish connection to Apache Kafka.
        
        This method creates the KafkaConsumer and establishes the connection.
        It should complete within 5 seconds as per NFR3.
        
        Raises:
            ConnectionError: If connection to Kafka fails
            ValueError: If connection parameters are invalid
        """
        if self._connected and self._consumer is not None:
            logger.debug("Already connected to Kafka")
            return
        
        try:
            start_time = time.time()
            
            # Create Kafka consumer with consumer group
            self._consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers.split(','),
                group_id=self.consumer_group,
                auto_offset_reset='latest',  # Start from latest if no offset
                enable_auto_commit=False,  # Manual commit for better control
                value_deserializer=lambda m: m.decode('utf-8') if m else None,
                consumer_timeout_ms=1000,  # Timeout for polling
            )
            
            # Test connection by getting partition metadata
            partitions = self._consumer.partitions_for_topic(self.topic)
            if partitions is None:
                raise ConnectionError(f"Topic {self.topic} not found or not accessible")
            
            self._connected = True
            elapsed = time.time() - start_time
            
            if elapsed > 5.0:
                logger.warning(
                    f"Connection took {elapsed:.2f}s (target: <5s)"
                )
            
            self._reconnect_attempts = 0
            logger.info(
                f"Successfully connected to Kafka: {self.topic} "
                f"(took {elapsed:.2f}s, partitions: {partitions})"
            )
            
        except Exception as e:
            self._connected = False
            error_msg = f"Failed to connect to Kafka: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ConnectionError(error_msg) from e
    
    def disconnect(self) -> None:
        """
        Close connection to Apache Kafka.
        
        This method gracefully closes the KafkaConsumer and cleans up resources.
        It is safe to call even if already disconnected.
        """
        if not self._connected and self._consumer is None:
            logger.debug("Already disconnected from Kafka")
            return
        
        try:
            if self._consumer is not None:
                self._consumer.close()
                self._consumer = None
            
            self._connected = False
            logger.info("Disconnected from Kafka")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}", exc_info=True)
            # Still mark as disconnected even if close failed
            self._connected = False
            self._consumer = None
    
    def is_connected(self) -> bool:
        """
        Check if currently connected to Kafka.
        
        Returns:
            True if connected and ready to consume messages, False otherwise
        """
        return self._connected and self._consumer is not None
    
    def consume_batch(
        self,
        max_messages: int = 100,
        timeout_ms: int = 1000
    ) -> Optional[MessageBatch]:
        """
        Consume a batch of messages from Kafka.
        
        This method retrieves messages from Kafka and returns them as a MessageBatch.
        It respects the max_messages limit and timeout_ms timeout. Message retrieval
        latency should not exceed 100ms for 95th percentile.
        
        Args:
            max_messages: Maximum number of messages to retrieve (default: 100)
            timeout_ms: Maximum time to wait for messages in milliseconds (default: 1000)
        
        Returns:
            MessageBatch containing messages, or None if no messages available
            within the timeout period
            
        Raises:
            ConnectionError: If not connected to Kafka
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Kafka. Call connect() first.")
        
        try:
            start_time = time.time()
            timeout_seconds = timeout_ms / 1000.0
            
            # Poll for messages
            message_pack = self._consumer.poll(
                timeout_ms=timeout_ms,
                max_records=max_messages
            )
            
            messages: List[Message] = []
            batch_id = str(uuid4())
            received_at = datetime.utcnow()
            
            # Convert Kafka messages to Message objects
            for topic_partition, records in message_pack.items():
                for record in records:
                    message = self._kafka_record_to_message(record)
                    messages.append(message)
                    
                    # Stop if we've reached max_messages
                    if len(messages) >= max_messages:
                        break
                
                if len(messages) >= max_messages:
                    break
            
            elapsed = time.time() - start_time
            
            if messages:
                batch = MessageBatch(
                    messages=messages,
                    batch_id=batch_id,
                    received_at=received_at,
                    broker_type="kafka"
                )
                
                logger.debug(
                    f"Consumed {len(messages)} messages in {elapsed*1000:.2f}ms"
                )
                
                # Check latency requirement (95th percentile < 100ms)
                if elapsed > 0.1:  # 100ms
                    logger.warning(
                        f"Message retrieval latency {elapsed*1000:.2f}ms "
                        f"exceeds 100ms target"
                    )
                
                return batch
            else:
                logger.debug(f"No messages available (timeout: {timeout_ms}ms)")
                return None
                
        except ConnectionError:
            raise
        except Exception as e:
            logger.error(f"Error consuming batch: {str(e)}", exc_info=True)
            # Attempt reconnection on error
            self._handle_connection_error()
            raise ConnectionError(f"Failed to consume batch: {str(e)}") from e
    
    def acknowledge_batch(self, batch: MessageBatch) -> None:
        """
        Acknowledge that a batch of messages has been successfully processed.
        
        For Kafka, this commits the offsets for the messages in the batch,
        preventing them from being reprocessed.
        
        Args:
            batch: MessageBatch that was successfully processed
            
        Raises:
            ConnectionError: If not connected to Kafka
            ValueError: If batch is invalid or empty
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Kafka")
        
        if not batch or batch.is_empty():
            raise ValueError("Cannot acknowledge empty batch")
        
        try:
            # Commit offsets for the batch
            # Note: Kafka consumer tracks offsets automatically during poll()
            # We commit synchronously to ensure offsets are persisted
            self._consumer.commit()
            
            logger.debug(
                f"Acknowledged batch {batch.batch_id} with {len(batch)} messages "
                f"(offsets committed)"
            )
            
        except Exception as e:
            logger.error(f"Failed to acknowledge batch: {str(e)}", exc_info=True)
            raise
    
    def checkpoint(self, batch: MessageBatch) -> None:
        """
        Create a recovery checkpoint for a batch of messages.
        
        This method commits Kafka offsets, allowing the consumer to resume
        processing from this point in case of failure. Consumer group
        coordination ensures multiple instances don't process the same messages.
        
        Args:
            batch: MessageBatch to checkpoint
            
        Raises:
            ConnectionError: If not connected to Kafka
            ValueError: If batch is invalid or empty
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Kafka")
        
        if not batch or batch.is_empty():
            raise ValueError("Cannot checkpoint empty batch")
        
        try:
            # Commit offsets synchronously for checkpoint
            self._consumer.commit()
            
            logger.info(
                f"Checkpointed batch {batch.batch_id} with {len(batch)} messages "
                f"(offsets committed to consumer group: {self.consumer_group})"
            )
            
        except Exception as e:
            logger.error(f"Failed to checkpoint batch: {str(e)}", exc_info=True)
            raise
    
    def _kafka_record_to_message(self, record) -> Message:
        """
        Convert Kafka ConsumerRecord to Message object.
        
        Args:
            record: Kafka ConsumerRecord
            
        Returns:
            Message object
        """
        # Extract message body
        body = record.value if record.value else ""
        
        # Extract headers (Kafka 0.11+)
        headers = {}
        if hasattr(record, 'headers') and record.headers:
            for key, value in record.headers:
                headers[key.decode('utf-8')] = value.decode('utf-8') if value else ""
        
        # Extract correlation ID from headers or generate one
        correlation_id = headers.get("correlation_id", str(uuid4()))
        
        # Extract timestamp
        timestamp = datetime.fromtimestamp(record.timestamp / 1000.0) if record.timestamp else datetime.utcnow()
        
        # Generate message ID
        message_id = headers.get("message_id", str(uuid4()))
        
        return Message(
            message_id=message_id,
            correlation_id=correlation_id,
            timestamp=timestamp,
            headers=headers,
            body=body,
            offset=record.offset,
            sequence_number=0  # Kafka doesn't have sequence numbers
        )
    
    def _handle_connection_error(self) -> None:
        """
        Handle connection errors with automatic reconnection.
        
        Implements exponential backoff retry strategy (base 2 seconds, max 30 seconds).
        """
        self._reconnect_attempts += 1
        
        if self._reconnect_attempts > self._max_reconnect_attempts:
            logger.error(
                f"Max reconnection attempts ({self._max_reconnect_attempts}) exceeded"
            )
            self._connected = False
            return
        
        # Calculate backoff (exponential: 2, 4, 8, 16, 30, 30, ...)
        backoff = min(
            self._base_backoff_seconds * (2 ** (self._reconnect_attempts - 1)),
            self._max_backoff_seconds
        )
        
        logger.warning(
            f"Connection error detected. Attempting reconnection "
            f"({self._reconnect_attempts}/{self._max_reconnect_attempts}) "
            f"in {backoff}s..."
        )
        
        time.sleep(backoff)
        
        try:
            self._connected = False
            self._consumer = None
            self.connect()
        except Exception as e:
            logger.error(f"Reconnection attempt failed: {str(e)}")

