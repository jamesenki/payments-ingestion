"""
Azure Event Hub publisher implementation.
"""

import asyncio
import json
import logging
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from azure.eventhub import EventData
    from azure.eventhub.aio import EventHubProducerClient
    from azure.identity.aio import DefaultAzureCredential
    AZURE_EVENTHUB_AVAILABLE = True
except ImportError:
    AZURE_EVENTHUB_AVAILABLE = False

from .base import BasePublisher
from .metrics import PublisherMetrics

logger = logging.getLogger(__name__)


class EventHubPublisher(BasePublisher):
    """
    Publisher for Azure Event Hubs with batching, retry logic, and metrics.
    
    Features:
    - Batch publishing for improved throughput
    - Exponential backoff retry logic
    - Connection pooling
    - Metrics collection
    - Managed identity and connection string authentication
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Event Hub publisher.
        
        Args:
            config: Configuration dictionary with:
                - connection_string: Event Hub connection string (optional)
                - fully_qualified_namespace: Event Hub namespace (optional)
                - eventhub_name: Event Hub name (optional)
                - batch_size: Batch size for publishing
                - max_retries: Maximum retry attempts
                - retry_delay: Initial retry delay in seconds
                - use_managed_identity: Use managed identity auth (default: False)
        """
        super().__init__(config)
        
        if not AZURE_EVENTHUB_AVAILABLE:
            raise ImportError(
                "azure-eventhub package not installed. "
                "Install with: pip install azure-eventhub"
            )
        
        self.connection_string = config.get("connection_string")
        self.fully_qualified_namespace = config.get("fully_qualified_namespace")
        self.eventhub_name = config.get("eventhub_name")
        self.use_managed_identity = config.get("use_managed_identity", False)
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
        
        # Validate configuration
        if not self.connection_string and not (self.fully_qualified_namespace and self.eventhub_name):
            raise ValueError(
                "Either connection_string or (fully_qualified_namespace + eventhub_name) must be provided"
            )
        
        self.client: Optional[Any] = None  # EventHubProducerClient when available
        self.metrics = PublisherMetrics()
        self._lock = asyncio.Lock()
    
    async def _get_client(self):
        """Get or create Event Hub client."""
        if self.client is not None:
            return self.client
        
        async with self._lock:
            if self.client is not None:
                return self.client
            
            try:
                if self.connection_string:
                    self.client = EventHubProducerClient.from_connection_string(
                        conn_str=self.connection_string,
                        eventhub_name=self.eventhub_name
                    )
                elif self.use_managed_identity:
                    credential = DefaultAzureCredential()
                    self.client = EventHubProducerClient(
                        fully_qualified_namespace=self.fully_qualified_namespace,
                        eventhub_name=self.eventhub_name,
                        credential=credential
                    )
                else:
                    raise ValueError("No authentication method configured")
                
                logger.info("Event Hub client created successfully")
                return self.client
            except Exception as e:
                logger.error(f"Failed to create Event Hub client: {e}")
                raise
    
    async def publish(self, transaction: Dict[str, Any]) -> bool:
        """
        Publish a single transaction.
        
        Args:
            transaction: Transaction data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        return await self.publish_batch([transaction]) == 1
    
    async def publish_batch(self, transactions: List[Dict[str, Any]]) -> int:
        """
        Publish a batch of transactions with retry logic.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Number of successfully published transactions
        """
        if not transactions:
            return 0
        
        start_time = time.time()
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                client = await self._get_client()
                
                # Create event data batch
                event_data_batch = await client.create_batch()
                
                for transaction in transactions:
                    # Serialize transaction to JSON
                    json_data = json.dumps(transaction, default=str)
                    event_data = EventData(json_data)
                    
                    # Add to batch
                    try:
                        event_data_batch.add(event_data)
                    except ValueError:
                        # Batch is full, send it and create a new one
                        await client.send_batch(event_data_batch)
                        self.metrics.record_batch(len(event_data_batch))
                        event_data_batch = await client.create_batch()
                        event_data_batch.add(event_data)
                
                # Send remaining events
                if len(event_data_batch) > 0:
                    await client.send_batch(event_data_batch)
                    self.metrics.record_batch(len(event_data_batch))
                
                # Record success
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.record_success(count=len(transactions), latency_ms=latency_ms)
                
                logger.debug(f"Published batch of {len(transactions)} transactions")
                return len(transactions)
                
            except Exception as e:
                retry_count += 1
                error_type = type(e).__name__
                
                if retry_count > self.max_retries:
                    # Max retries exceeded
                    logger.error(f"Failed to publish batch after {self.max_retries} retries: {e}")
                    self.metrics.record_failure(error_type=error_type, retry_count=retry_count - 1)
                    return 0
                
                # Exponential backoff
                delay = self.retry_delay * (2 ** (retry_count - 1))
                logger.warning(
                    f"Publish failed (attempt {retry_count}/{self.max_retries}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
        
        return 0
    
    async def close(self):
        """Close the Event Hub client."""
        if self.client is not None:
            try:
                await self.client.close()
                logger.info("Event Hub client closed")
            except Exception as e:
                logger.error(f"Error closing Event Hub client: {e}")
            finally:
                self.client = None
    
    def get_metrics(self) -> Dict:
        """Get publisher metrics."""
        return self.metrics.get_summary()
    
    def reset_metrics(self):
        """Reset metrics."""
        self.metrics.reset()

