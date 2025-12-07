"""
Blob Storage implementation for raw event storage.

Implements WO-64: Batched Blob Storage Service with Parquet Operations
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from threading import Lock, Timer
from uuid import uuid4

from azure.storage.blob import BlobClient, BlobServiceClient
from azure.core.exceptions import AzureError

from .raw_event import RawEvent, BufferError, StorageError
from .parquet_serializer import ParquetSerializer
from .raw_event_store import RawEventStore


logger = logging.getLogger(__name__)


class BlobRawEventStore(RawEventStore):
    """
    Buffered blob storage service for raw events with Parquet serialization.
    
    This class buffers events in memory and periodically flushes them as
    Parquet files to Azure Blob Storage for efficient archival storage.
    
    Features:
    - Automatic buffering with configurable batch size and flush interval
    - Parquet serialization for efficient columnar storage
    - Retry logic with exponential backoff
    - Dead-letter queue routing for failed events
    - Thread-safe concurrent operations
    """
    
    def __init__(
        self,
        connection_string: str,
        container_name: str = "raw-events",
        batch_size: int = 1000,
        flush_interval_seconds: int = 30,
        max_buffer_size: int = 5000,
        compression: str = "snappy"
    ):
        """
        Initialize BlobRawEventStore.
        
        Args:
            connection_string: Azure Storage account connection string
            container_name: Blob container name for raw events
            batch_size: Number of events to buffer before auto-flush
            flush_interval_seconds: Maximum time to wait before flushing buffer
            max_buffer_size: Maximum buffer size before forced flush
            compression: Parquet compression algorithm
        """
        self.connection_string = connection_string
        self.container_name = container_name
        self.batch_size = batch_size
        self.flush_interval_seconds = flush_interval_seconds
        self.max_buffer_size = max_buffer_size
        self.compression = compression
        
        # Initialize Azure Blob Service Client
        self.blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        
        # Initialize Parquet serializer
        self.serializer = ParquetSerializer(compression=compression)
        
        # Buffer management
        self._buffer: List[RawEvent] = []
        self._buffer_lock = Lock()
        self._last_flush_time = datetime.utcnow()
        self._flush_timer: Optional[Timer] = None
        
        # Metrics
        self._events_stored = 0
        self._events_failed = 0
        self._batches_flushed = 0
        self._last_error: Optional[str] = None
        
        logger.info(
            f"BlobRawEventStore initialized: container={container_name}, "
            f"batch_size={batch_size}, flush_interval={flush_interval_seconds}s"
        )
    
    def store_event(self, event: RawEvent) -> Optional[str]:
        """
        Store a single raw event (buffered, may not return ID immediately).
        
        Args:
            event: RawEvent to store
            
        Returns:
            None (events are buffered and flushed in batches)
        """
        self.buffer_event(event)
        return None
    
    def store_events_batch(self, events: List[RawEvent]) -> List[str]:
        """
        Store multiple raw events in a batch.
        
        Args:
            events: List of RawEvent objects to store
            
        Returns:
            Empty list (events are buffered and flushed in batches)
        """
        for event in events:
            self.buffer_event(event)
        return []
    
    def flush(self) -> int:
        """
        Flush any buffered events to storage.
        
        Returns:
            Number of events flushed
        """
        return self.flush_buffer()
    
    def buffer_event(self, event: RawEvent) -> None:
        """
        Add event to in-memory buffer and auto-flush if needed.
        
        This method is thread-safe and supports concurrent writes from
        multiple Azure Function instances.
        
        Args:
            event: RawEvent to buffer
            
        Raises:
            BufferError: If buffer operations fail
        """
        try:
            with self._buffer_lock:
                self._buffer.append(event)
                buffer_size = len(self._buffer)
                
                # Check if buffer needs immediate flush
                if buffer_size >= self.max_buffer_size:
                    logger.warning(
                        f"Buffer overflow protection: flushing {buffer_size} events "
                        f"(max={self.max_buffer_size})"
                    )
                    self._flush_buffer_unsafe()
                elif buffer_size >= self.batch_size:
                    # Auto-flush when batch size reached
                    logger.debug(f"Batch size reached ({buffer_size}), flushing buffer")
                    self._flush_buffer_unsafe()
                else:
                    # Start/reset flush timer if this is the first event in buffer
                    if buffer_size == 1:
                        self._start_flush_timer()
        
        except Exception as e:
            logger.error(f"Failed to buffer event: {str(e)}", exc_info=True)
            raise BufferError(f"Failed to buffer event: {str(e)}") from e
    
    def flush_buffer(self) -> int:
        """
        Flush buffered events to Blob Storage as Parquet file.
        
        This method serializes all buffered events to Parquet format and
        uploads them to Azure Blob Storage with date-based path structure.
        
        Returns:
            Number of events flushed
            
        Raises:
            StorageError: If flush operation fails
        """
        with self._buffer_lock:
            return self._flush_buffer_unsafe()
    
    def _flush_buffer_unsafe(self) -> int:
        """
        Internal flush method (not thread-safe, must be called with lock).
        
        Returns:
            Number of events flushed
        """
        if not self._buffer:
            return 0
        
        events_to_flush = self._buffer.copy()
        self._buffer.clear()
        self._stop_flush_timer()
        
        if not events_to_flush:
            return 0
        
        try:
            # Serialize events to Parquet
            parquet_bytes = self.serializer.serialize_events(events_to_flush)
            
            # Generate blob path with date-based structure
            blob_path = self._generate_blob_path()
            
            # Upload to Blob Storage with retry logic
            self._upload_with_retry(blob_path, parquet_bytes, events_to_flush)
            
            # Update metrics
            event_count = len(events_to_flush)
            self._events_stored += event_count
            self._batches_flushed += 1
            self._last_flush_time = datetime.utcnow()
            
            # Extract correlation IDs for logging
            correlation_ids = [str(event.correlation_id) for event in events_to_flush]
            
            logger.info(
                f"Successfully flushed {event_count} events to {blob_path}. "
                f"Correlation IDs: {correlation_ids[:5]}{'...' if len(correlation_ids) > 5 else ''}"
            )
            
            return event_count
            
        except BufferError as e:
            # Serialization error - route to dead-letter queue
            logger.error(f"Serialization error during flush: {str(e)}")
            self._route_to_dead_letter_queue(events_to_flush, f"Serialization error: {str(e)}")
            raise StorageError(f"Failed to serialize events: {str(e)}") from e
            
        except Exception as e:
            # Other errors - route to dead-letter queue
            logger.error(f"Storage error during flush: {str(e)}", exc_info=True)
            self._route_to_dead_letter_queue(events_to_flush, f"Storage error: {str(e)}")
            raise StorageError(f"Failed to flush buffer: {str(e)}") from e
    
    def _generate_blob_path(self) -> str:
        """
        Generate blob path with date-based structure.
        
        Format: raw_events/yyyy={year}/mm={month}/dd={day}/events_{timestamp}.parquet
        
        Returns:
            Blob path string
        """
        now = datetime.utcnow()
        timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
        
        # Add unique identifier to prevent collisions in concurrent scenarios
        unique_id = str(uuid4())[:8]
        
        path = (
            f"raw_events/"
            f"yyyy={now.year:04d}/"
            f"mm={now.month:02d}/"
            f"dd={now.day:02d}/"
            f"events_{timestamp}_{unique_id}.parquet"
        )
        
        return path
    
    def _upload_with_retry(
        self,
        blob_path: str,
        parquet_bytes: bytes,
        events: List[RawEvent],
        max_retries: int = 3
    ) -> None:
        """
        Upload Parquet bytes to Blob Storage with retry logic.
        
        Implements exponential backoff retry strategy for transient errors.
        
        Args:
            blob_path: Blob path for upload
            parquet_bytes: Serialized Parquet bytes
            events: Original events (for error reporting)
            max_retries: Maximum number of retry attempts
            
        Raises:
            StorageError: If upload fails after all retries
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_path
        )
        
        retry_delays = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s
        
        for attempt in range(max_retries + 1):
            try:
                # Upload with overwrite=False to prevent collisions
                blob_client.upload_blob(
                    data=parquet_bytes,
                    overwrite=False,
                    content_settings=None,
                    metadata={
                        "event_count": str(len(events)),
                        "uploaded_at": datetime.utcnow().isoformat(),
                        "compression": self.compression,
                    }
                )
                
                logger.debug(f"Successfully uploaded {blob_path} (attempt {attempt + 1})")
                return
                
            except AzureError as e:
                # Check if it's a transient error
                if self._is_transient_error(e) and attempt < max_retries:
                    delay = retry_delays[attempt]
                    logger.warning(
                        f"Transient error uploading {blob_path} (attempt {attempt + 1}/{max_retries + 1}): "
                        f"{str(e)}. Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    # Permanent error or max retries exceeded
                    error_msg = f"Failed to upload {blob_path} after {attempt + 1} attempts: {str(e)}"
                    logger.error(error_msg)
                    raise StorageError(error_msg) from e
            
            except Exception as e:
                # Unexpected error
                error_msg = f"Unexpected error uploading {blob_path}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise StorageError(error_msg) from e
        
        # Should not reach here, but handle just in case
        raise StorageError(f"Failed to upload {blob_path} after {max_retries + 1} attempts")
    
    def _is_transient_error(self, error: AzureError) -> bool:
        """
        Determine if an Azure error is transient and should be retried.
        
        Args:
            error: AzureError to check
            
        Returns:
            True if error is transient, False otherwise
        """
        # Transient errors: timeouts, service unavailable, throttling
        transient_status_codes = [408, 429, 500, 502, 503, 504]
        
        if hasattr(error, 'status_code'):
            return error.status_code in transient_status_codes
        
        # Check error message for transient indicators
        error_str = str(error).lower()
        transient_indicators = [
            'timeout',
            'service unavailable',
            'throttl',
            'temporary',
            'retry',
            'connection',
        ]
        
        return any(indicator in error_str for indicator in transient_indicators)
    
    def _route_to_dead_letter_queue(
        self,
        events: List[RawEvent],
        failure_reason: str
    ) -> None:
        """
        Route failed events to dead-letter queue (PostgreSQL failed_items table).
        
        This method should be implemented to insert failed events into the
        failed_items table for investigation and potential replay.
        
        Args:
            events: Events that failed to store
            failure_reason: Reason for failure
        """
        # TODO: Implement connection to PostgreSQL failed_items table
        # This will be implemented when database connection layer is available
        
        self._events_failed += len(events)
        self._last_error = failure_reason
        
        logger.error(
            f"Routed {len(events)} events to dead-letter queue. "
            f"Reason: {failure_reason}. "
            f"Transaction IDs: {[e.transaction_id for e in events[:5]]}"
        )
        
        # For now, just log the events that would be stored
        # In production, this would insert into failed_items table
    
    def _start_flush_timer(self) -> None:
        """Start timer for automatic flush based on flush_interval_seconds."""
        if self._flush_timer is not None:
            self._flush_timer.cancel()
        
        def flush_callback():
            logger.debug(f"Flush timer expired, flushing buffer")
            self.flush_buffer()
        
        self._flush_timer = Timer(self.flush_interval_seconds, flush_callback)
        self._flush_timer.daemon = True
        self._flush_timer.start()
    
    def _stop_flush_timer(self) -> None:
        """Stop the flush timer."""
        if self._flush_timer is not None:
            self._flush_timer.cancel()
            self._flush_timer = None
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get storage operation metrics.
        
        Returns:
            Dictionary with metrics including events stored, failed, batches flushed, etc.
        """
        with self._buffer_lock:
            buffer_size = len(self._buffer)
        
        return {
            "events_stored": self._events_stored,
            "events_failed": self._events_failed,
            "batches_flushed": self._batches_flushed,
            "current_buffer_size": buffer_size,
            "last_flush_time": self._last_flush_time.isoformat() if self._last_flush_time else None,
            "last_error": self._last_error,
        }
    
    def get_events_by_date(self, target_date: datetime) -> List[RawEvent]:
        """
        Retrieve all RawEvent objects for a specific date.
        
        This method scans Parquet files in the date-based blob path pattern
        (raw_events/yyyy={year}/mm={month}/dd={day}/) and deserializes all
        events from matching files.
        
        Args:
            target_date: Target date (datetime object, time component ignored)
            
        Returns:
            List of RawEvent objects for the specified date
            
        Raises:
            StorageError: If retrieval fails
        """
        try:
            # Generate date-based prefix path
            date_prefix = (
                f"raw_events/"
                f"yyyy={target_date.year:04d}/"
                f"mm={target_date.month:02d}/"
                f"dd={target_date.day:02d}/"
            )
            
            logger.info(f"Retrieving events for date: {target_date.date()}, prefix: {date_prefix}")
            
            # List all blobs matching the date prefix
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            
            blobs = container_client.list_blobs(name_starts_with=date_prefix)
            
            events = []
            blob_count = 0
            
            for blob in blobs:
                blob_count += 1
                try:
                    # Download blob content
                    blob_client = self.blob_service_client.get_blob_client(
                        container=self.container_name,
                        blob=blob.name
                    )
                    
                    blob_data = blob_client.download_blob().readall()
                    
                    # Deserialize Parquet bytes to events
                    file_events = self.serializer.deserialize_events(blob_data)
                    events.extend(file_events)
                    
                    logger.debug(
                        f"Retrieved {len(file_events)} events from {blob.name}"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Failed to read blob {blob.name}: {str(e)}",
                        exc_info=True
                    )
                    # Continue with other blobs even if one fails
                    continue
            
            logger.info(
                f"Retrieved {len(events)} events from {blob_count} blobs for date {target_date.date()}"
            )
            
            return events
            
        except AzureError as e:
            error_msg = f"Azure error retrieving events for date {target_date.date()}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error retrieving events for date {target_date.date()}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise StorageError(error_msg) from e
    
    def get_events_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[RawEvent]:
        """
        Retrieve RawEvent objects within a time range.
        
        This method scans relevant date partitions and filters events by
        created_at timestamp to return only events within the specified range.
        
        Args:
            start_time: Start of time range (inclusive)
            end_time: End of time range (inclusive)
            
        Returns:
            List of RawEvent objects within the time range
            
        Raises:
            StorageError: If retrieval fails
            ValueError: If start_time > end_time
        """
        if start_time > end_time:
            raise ValueError(f"start_time ({start_time}) must be <= end_time ({end_time})")
        
        try:
            logger.info(
                f"Retrieving events for time range: {start_time} to {end_time}"
            )
            
            # Generate list of date prefixes to scan
            date_prefixes = self._generate_date_prefixes(start_time, end_time)
            
            events = []
            total_blobs = 0
            
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            
            # Scan each date partition
            for date_prefix in date_prefixes:
                try:
                    blobs = container_client.list_blobs(name_starts_with=date_prefix)
                    
                    for blob in blobs:
                        total_blobs += 1
                        try:
                            # Download blob content
                            blob_client = self.blob_service_client.get_blob_client(
                                container=self.container_name,
                                blob=blob.name
                            )
                            
                            blob_data = blob_client.download_blob().readall()
                            
                            # Deserialize Parquet bytes to events
                            file_events = self.serializer.deserialize_events(blob_data)
                            
                            # Filter events by timestamp range
                            filtered_events = [
                                event for event in file_events
                                if start_time <= event.created_at <= end_time
                            ]
                            
                            events.extend(filtered_events)
                            
                            logger.debug(
                                f"Retrieved {len(filtered_events)}/{len(file_events)} events "
                                f"from {blob.name} (filtered by time range)"
                            )
                            
                        except Exception as e:
                            logger.error(
                                f"Failed to read blob {blob.name}: {str(e)}",
                                exc_info=True
                            )
                            # Continue with other blobs even if one fails
                            continue
                
                except Exception as e:
                    logger.error(
                        f"Failed to scan date prefix {date_prefix}: {str(e)}",
                        exc_info=True
                    )
                    # Continue with other date prefixes even if one fails
                    continue
            
            # Sort events by created_at timestamp
            events.sort(key=lambda e: e.created_at)
            
            logger.info(
                f"Retrieved {len(events)} events from {total_blobs} blobs "
                f"for time range {start_time} to {end_time}"
            )
            
            return events
            
        except AzureError as e:
            error_msg = (
                f"Azure error retrieving events for time range "
                f"{start_time} to {end_time}: {str(e)}"
            )
            logger.error(error_msg, exc_info=True)
            raise StorageError(error_msg) from e
            
        except Exception as e:
            error_msg = (
                f"Unexpected error retrieving events for time range "
                f"{start_time} to {end_time}: {str(e)}"
            )
            logger.error(error_msg, exc_info=True)
            raise StorageError(error_msg) from e
    
    def _generate_date_prefixes(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[str]:
        """
        Generate list of date-based blob prefixes for the time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of blob path prefixes (e.g., ["raw_events/yyyy=2025/mm=12/dd=05/"])
        """
        prefixes = []
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            prefix = (
                f"raw_events/"
                f"yyyy={current_date.year:04d}/"
                f"mm={current_date.month:02d}/"
                f"dd={current_date.day:02d}/"
            )
            prefixes.append(prefix)
            
            # Move to next day
            current_date += timedelta(days=1)
        
        return prefixes
    
    def close(self) -> None:
        """
        Close the store and flush any remaining buffered events.
        
        This should be called during graceful shutdown to ensure no events are lost.
        """
        logger.info("Closing BlobRawEventStore, flushing remaining events...")
        
        self._stop_flush_timer()
        remaining = self.flush_buffer()
        
        if remaining > 0:
            logger.info(f"Flushed {remaining} remaining events during close")
        
        # Close blob service client
        if self.blob_service_client:
            # Azure SDK doesn't have explicit close, but we can clear references
            self.blob_service_client = None
        
        logger.info("BlobRawEventStore closed")

