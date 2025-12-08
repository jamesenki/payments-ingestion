"""
Azure Function entry point for payment transaction processing.

Implements WO-11: Implement Main Azure Function Entry Point Script

This module provides the main Azure Function entry point that orchestrates the
complete payment transaction processing workflow:
1. Store raw events to Blob Storage (Parquet)
2. Store extracted metrics to PostgreSQL dynamic_metrics
3. Update aggregate metrics in PostgreSQL (payment_metrics_5m and aggregate_histograms)
"""

import json
import logging
import os
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

# Azure Functions imports (with fallback for local testing)
try:
    import azure.functions as func
    AZURE_FUNCTIONS_AVAILABLE = True
except ImportError:
    AZURE_FUNCTIONS_AVAILABLE = False
    # Create mock classes for local testing
    class func:
        class EventHubEvent:
            def __init__(self, body: bytes, properties: Dict[str, Any] = None):
                self._body = body
                self._properties = properties or {}
            
            def get_body(self) -> bytes:
                return self._body
            
            def get_properties(self) -> Dict[str, Any]:
                return self._properties
        
        @staticmethod
        def EventHubMessageTrigger(*args, **kwargs):
            """Mock decorator for local testing."""
            def decorator(fn):
                return fn
            return decorator

from .parsing.data_parser import DataParser
from .parsing.models import ParsedTransaction, ParseResult
from .storage.raw_event import RawEvent
from .connections.hybrid_storage import HybridStorageConnectionManager
from .messaging import Message

# Conditional import for BlobRawEventStore (requires Azure SDK)
try:
    from .storage.blob_raw_event_store import BlobRawEventStore
    BLOB_STORAGE_AVAILABLE = True
except ImportError:
    BLOB_STORAGE_AVAILABLE = False
    BlobRawEventStore = None

logger = logging.getLogger(__name__)

# Global connection manager (initialized on first function invocation)
_connection_manager: Optional[HybridStorageConnectionManager] = None
_blob_store: Optional[BlobRawEventStore] = None
_parser: Optional[DataParser] = None


def _get_connection_manager() -> HybridStorageConnectionManager:
    """Get or initialize the hybrid storage connection manager."""
    global _connection_manager
    
    if _connection_manager is None:
        postgres_conn_str = os.getenv(
            "POSTGRES_CONNECTION_STRING",
            os.getenv("AzureWebJobsStorage")  # Fallback for local testing
        )
        blob_conn_str = os.getenv(
            "BLOB_STORAGE_CONNECTION_STRING",
            os.getenv("AzureWebJobsStorage")  # Fallback for local testing
        )
        
        if not postgres_conn_str or not blob_conn_str:
            raise ValueError(
                "POSTGRES_CONNECTION_STRING and BLOB_STORAGE_CONNECTION_STRING "
                "must be set"
            )
        
        _connection_manager = HybridStorageConnectionManager(
            postgres_connection_string=postgres_conn_str,
            blob_storage_connection_string=blob_conn_str
        )
        _connection_manager.initialize()
        
        logger.info("HybridStorageConnectionManager initialized")
    
    return _connection_manager


def _get_blob_store():
    """Get or initialize the blob storage service."""
    global _blob_store
    
    if not BLOB_STORAGE_AVAILABLE:
        raise ImportError(
            "azure-storage-blob package is required for blob storage. "
            "Install with: pip install azure-storage-blob"
        )
    
    if _blob_store is None:
        conn_manager = _get_connection_manager()
        blob_conn_str = os.getenv(
            "BLOB_STORAGE_CONNECTION_STRING",
            os.getenv("AzureWebJobsStorage")
        )
        container_name = os.getenv("BLOB_CONTAINER_NAME", "raw-events")
        
        _blob_store = BlobRawEventStore(
            connection_string=blob_conn_str,
            container_name=container_name,
            batch_size=int(os.getenv("BLOB_BATCH_SIZE", "1000")),
            flush_interval_seconds=int(os.getenv("BLOB_FLUSH_INTERVAL", "30"))
        )
        
        logger.info(f"BlobRawEventStore initialized: container={container_name}")
    
    return _blob_store


def _get_parser() -> DataParser:
    """Get or initialize the data parser."""
    global _parser
    
    if _parser is None:
        _parser = DataParser()
        logger.info("DataParser initialized")
    
    return _parser


def _store_raw_event_to_blob(
    transaction: ParsedTransaction,
    correlation_id: UUID,
    raw_payload: Dict[str, Any]
) -> Optional[str]:
    """
    Store raw transaction event to Blob Storage as Parquet.
    
    Args:
        transaction: Parsed transaction
        correlation_id: Correlation ID for tracing
        raw_payload: Original transaction payload
        
    Returns:
        Blob path if successful, None otherwise
    """
    try:
        blob_store = _get_blob_store()
        
        # Create RawEvent from parsed transaction
        raw_event = RawEvent(
            transaction_id=transaction.transaction_id,
            correlation_id=correlation_id,
            event_payload=raw_payload,
            created_at=datetime.utcnow()
        )
        
        # Store event (buffered, will flush automatically)
        blob_path = blob_store.store_event(raw_event)
        
        logger.debug(
            f"Raw event stored to blob: transaction_id={transaction.transaction_id}, "
            f"correlation_id={correlation_id}"
        )
        
        return blob_path
        
    except Exception as e:
        logger.error(
            f"Failed to store raw event to blob: {e}",
            exc_info=True,
            extra={
                "transaction_id": transaction.transaction_id,
                "correlation_id": str(correlation_id)
            }
        )
        return None


def _store_dynamic_metrics(
    transaction: ParsedTransaction,
    correlation_id: UUID,
    metrics: List[Dict[str, Any]]
) -> bool:
    """
    Store extracted metrics to PostgreSQL dynamic_metrics table.
    
    Args:
        transaction: Parsed transaction
        correlation_id: Correlation ID for tracing
        metrics: List of metric dictionaries with keys: metric_type, metric_value, metric_data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn_manager = _get_connection_manager()
        conn = conn_manager.get_postgres_connection()
        
        try:
            cursor = conn.cursor()
            
            for metric in metrics:
                cursor.execute("""
                    INSERT INTO dynamic_metrics (
                        transaction_id,
                        correlation_id,
                        metric_type,
                        metric_value,
                        metric_data,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    transaction.transaction_id,
                    str(correlation_id),
                    metric.get("metric_type", "unknown"),
                    metric.get("metric_value"),
                    json.dumps(metric.get("metric_data", {})),
                    datetime.utcnow()
                ))
            
            conn.commit()
            logger.debug(
                f"Dynamic metrics stored: transaction_id={transaction.transaction_id}, "
                f"count={len(metrics)}"
            )
            return True
            
        finally:
            conn_manager.release_postgres_connection(conn)
            
    except Exception as e:
        logger.error(
            f"Failed to store dynamic metrics: {e}",
            exc_info=True,
            extra={
                "transaction_id": transaction.transaction_id,
                "correlation_id": str(correlation_id)
            }
        )
        return False


def _update_payment_metrics_5m(transaction: ParsedTransaction) -> bool:
    """
    Update payment_metrics_5m table with 5-minute window aggregates.
    
    Args:
        transaction: Parsed transaction
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn_manager = _get_connection_manager()
        conn = conn_manager.get_postgres_connection()
        
        try:
            # Calculate 5-minute window start
            window_start = transaction.timestamp.replace(
                minute=(transaction.timestamp.minute // 5) * 5,
                second=0,
                microsecond=0
            )
            window_end = window_start.replace(minute=window_start.minute + 5)
            
            cursor = conn.cursor()
            
            # Extract payment method and status from metadata
            payment_method = transaction.metadata.get("payment_method", "unknown")
            payment_status = str(transaction.status.value)
            
            # UPSERT operation
            cursor.execute("""
                INSERT INTO payment_metrics_5m (
                    window_start,
                    window_end,
                    payment_method,
                    currency,
                    payment_status,
                    total_count,
                    total_amount,
                    avg_amount,
                    min_amount,
                    max_amount,
                    created_at,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, 1, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (window_start, payment_method, currency, payment_status)
                DO UPDATE SET
                    total_count = payment_metrics_5m.total_count + 1,
                    total_amount = payment_metrics_5m.total_amount + EXCLUDED.total_amount,
                    avg_amount = (payment_metrics_5m.total_amount + EXCLUDED.total_amount) 
                                 / (payment_metrics_5m.total_count + 1),
                    min_amount = LEAST(payment_metrics_5m.min_amount, EXCLUDED.min_amount),
                    max_amount = GREATEST(payment_metrics_5m.max_amount, EXCLUDED.max_amount),
                    updated_at = EXCLUDED.updated_at
            """, (
                window_start,
                window_end,
                payment_method,
                transaction.currency,
                payment_status,
                transaction.amount,
                transaction.amount,
                transaction.amount,
                transaction.amount,
                datetime.utcnow(),
                datetime.utcnow()
            ))
            
            conn.commit()
            logger.debug(
                f"Payment metrics 5m updated: window_start={window_start}, "
                f"transaction_id={transaction.transaction_id}"
            )
            return True
            
        finally:
            conn_manager.release_postgres_connection(conn)
            
    except Exception as e:
        logger.error(
            f"Failed to update payment_metrics_5m: {e}",
            exc_info=True,
            extra={"transaction_id": transaction.transaction_id}
        )
        return False


def _update_aggregate_histograms(
    transaction: ParsedTransaction,
    metrics: List[Dict[str, Any]],
    correlation_id: UUID
) -> bool:
    """
    Update aggregate_histograms table with flexible window aggregates.
    
    Args:
        transaction: Parsed transaction
        metrics: List of extracted metrics
        correlation_id: Correlation ID for tracing
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn_manager = _get_connection_manager()
        conn = conn_manager.get_postgres_connection()
        
        try:
            # Use 5-minute windows for consistency
            window_start = transaction.timestamp.replace(
                minute=(transaction.timestamp.minute // 5) * 5,
                second=0,
                microsecond=0
            )
            window_end = window_start.replace(minute=window_start.minute + 5)
            
            cursor = conn.cursor()
            
            # Update histogram for each metric type
            for metric in metrics:
                metric_type = metric.get("metric_type", "unknown")
                event_type = transaction.transaction_type
                
                cursor.execute("""
                    INSERT INTO aggregate_histograms (
                        metric_type,
                        event_type,
                        time_window_start,
                        time_window_end,
                        event_count,
                        created_at,
                        updated_at
                    ) VALUES (%s, %s, %s, %s, 1, %s, %s)
                    ON CONFLICT (metric_type, event_type, time_window_start, time_window_end)
                    DO UPDATE SET
                        event_count = aggregate_histograms.event_count + 1,
                        updated_at = EXCLUDED.updated_at
                """, (
                    metric_type,
                    event_type,
                    window_start,
                    window_end,
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
            
            conn.commit()
            logger.debug(
                f"Aggregate histograms updated: window_start={window_start}, "
                f"transaction_id={transaction.transaction_id}"
            )
            return True
            
        finally:
            conn_manager.release_postgres_connection(conn)
            
    except Exception as e:
        logger.error(
            f"Failed to update aggregate_histograms: {e}",
            exc_info=True,
            extra={"transaction_id": transaction.transaction_id}
        )
        return False


def _route_to_dead_letter_queue(
    transaction_id: str,
    correlation_id: UUID,
    error_type: str,
    error_message: str,
    raw_payload: Dict[str, Any]
) -> bool:
    """
    Route failed transaction to dead-letter queue (failed_items table).
    
    Args:
        transaction_id: Transaction ID
        correlation_id: Correlation ID
        error_type: Type of error
        error_message: Error message
        raw_payload: Original transaction payload
        
    Returns:
        True if successful, False otherwise
    """
    try:
        conn_manager = _get_connection_manager()
        conn = conn_manager.get_postgres_connection()
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO failed_items (
                    transaction_id,
                    correlation_id,
                    error_type,
                    error_message,
                    raw_payload,
                    failed_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                transaction_id,
                str(correlation_id),
                error_type,
                error_message,
                json.dumps(raw_payload),
                datetime.utcnow()
            ))
            
            conn.commit()
            logger.info(
                f"Failed item routed to dead-letter queue: transaction_id={transaction_id}, "
                f"error_type={error_type}"
            )
            return True
            
        finally:
            conn_manager.release_postgres_connection(conn)
            
    except Exception as e:
        logger.error(
            f"Failed to route to dead-letter queue: {e}",
            exc_info=True,
            extra={"transaction_id": transaction_id}
        )
        return False


def _extract_metrics(transaction: ParsedTransaction) -> List[Dict[str, Any]]:
    """
    Extract metrics from parsed transaction.
    
    This is a simplified version. In production, this would use the MetricEngine.
    
    Args:
        transaction: Parsed transaction
        
    Returns:
        List of metric dictionaries
    """
    metrics = []
    
    # Basic transaction metrics
    metrics.append({
        "metric_type": "transaction_amount",
        "metric_value": transaction.amount,
        "metric_data": {
            "currency": transaction.currency,
            "status": str(transaction.status.value)
        }
    })
    
    # Channel metrics
    metrics.append({
        "metric_type": "channel_usage",
        "metric_value": 1,
        "metric_data": {
            "channel": transaction.channel,
            "transaction_type": transaction.transaction_type
        }
    })
    
    # Status metrics
    metrics.append({
        "metric_type": "transaction_status",
        "metric_value": 1,
        "metric_data": {
            "status": str(transaction.status.value),
            "transaction_type": transaction.transaction_type
        }
    })
    
    return metrics


@func.EventHubMessageTrigger(
    arg_name="events",
    event_hub_name="payments-ingestion-{env}-evh-eus",
    connection="EventHubConnectionString"
)
def process_payment_transactions(events: func.EventHubEvent) -> None:
    """
    Azure Function entry point for processing payment transactions.
    
    This function is triggered by Event Hub messages and orchestrates the
    complete payment transaction processing workflow:
    1. Parse and validate transaction
    2. Store raw event to Blob Storage (Parquet)
    3. Extract and store metrics to PostgreSQL dynamic_metrics
    4. Update aggregate metrics in PostgreSQL (payment_metrics_5m and aggregate_histograms)
    
    Args:
        events: Event Hub event(s) containing transaction data
    """
    correlation_id = uuid4()
    start_time = datetime.utcnow()
    
    try:
        # Get event body
        if isinstance(events, list):
            event_bodies = [evt.get_body() for evt in events]
        else:
            event_bodies = [events.get_body()]
        
        # Process each event
        for event_body in event_bodies:
            try:
                # Parse event body
                if isinstance(event_body, bytes):
                    raw_payload = json.loads(event_body.decode('utf-8'))
                else:
                    raw_payload = event_body if isinstance(event_body, dict) else json.loads(event_body)
                
                # Parse and validate transaction
                parser = _get_parser()
                message_body = json.dumps(raw_payload)
                parse_result: ParseResult = parser.parse_and_validate(message_body)
                
                if not parse_result.success:
                    # Route to dead-letter queue
                    _route_to_dead_letter_queue(
                        transaction_id=raw_payload.get("transaction_id", "unknown"),
                        correlation_id=correlation_id,
                        error_type="validation_error",
                        error_message=str(parse_result.error),
                        raw_payload=raw_payload
                    )
                    continue
                
                transaction: ParsedTransaction = parse_result.transaction
                
                # 1. Store raw event to Blob Storage
                blob_path = _store_raw_event_to_blob(
                    transaction=transaction,
                    correlation_id=correlation_id,
                    raw_payload=raw_payload
                )
                
                if blob_path is None:
                    logger.warning(
                        f"Failed to store raw event, continuing with metrics: "
                        f"transaction_id={transaction.transaction_id}"
                    )
                
                # 2. Extract metrics
                metrics = _extract_metrics(transaction)
                
                # 3. Store dynamic metrics
                metrics_stored = _store_dynamic_metrics(
                    transaction=transaction,
                    correlation_id=correlation_id,
                    metrics=metrics
                )
                
                if not metrics_stored:
                    logger.warning(
                        f"Failed to store dynamic metrics: "
                        f"transaction_id={transaction.transaction_id}"
                    )
                
                # 4. Update payment_metrics_5m
                payment_metrics_updated = _update_payment_metrics_5m(transaction)
                
                if not payment_metrics_updated:
                    logger.warning(
                        f"Failed to update payment_metrics_5m: "
                        f"transaction_id={transaction.transaction_id}"
                    )
                
                # 5. Update aggregate_histograms
                histograms_updated = _update_aggregate_histograms(
                    transaction=transaction,
                    metrics=metrics,
                    correlation_id=correlation_id
                )
                
                if not histograms_updated:
                    logger.warning(
                        f"Failed to update aggregate_histograms: "
                        f"transaction_id={transaction.transaction_id}"
                    )
                
                # Log success
                elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.info(
                    f"Transaction processed successfully: "
                    f"transaction_id={transaction.transaction_id}, "
                    f"correlation_id={correlation_id}, "
                    f"elapsed_ms={elapsed_ms:.2f}"
                )
                
            except Exception as e:
                # Route to dead-letter queue
                transaction_id = raw_payload.get("transaction_id", "unknown") if 'raw_payload' in locals() else "unknown"
                _route_to_dead_letter_queue(
                    transaction_id=transaction_id,
                    correlation_id=correlation_id,
                    error_type="processing_error",
                    error_message=f"{type(e).__name__}: {str(e)}",
                    raw_payload=raw_payload if 'raw_payload' in locals() else {}
                )
                
                logger.error(
                    f"Failed to process transaction: {e}",
                    exc_info=True,
                    extra={
                        "transaction_id": transaction_id,
                        "correlation_id": str(correlation_id)
                    }
                )
        
    except Exception as e:
        logger.error(
            f"Critical error in process_payment_transactions: {e}",
            exc_info=True,
            extra={"correlation_id": str(correlation_id)}
        )
        raise


# Local testing function (non-Azure Functions entry point)
def process_transaction_local(event_body: bytes | str | dict) -> Dict[str, Any]:
    """
    Local testing function for processing transactions without Azure Functions runtime.
    
    Args:
        event_body: Transaction data (bytes, str, or dict)
        
    Returns:
        Dictionary with processing results
    """
    correlation_id = uuid4()
    start_time = datetime.utcnow()
    
    result = {
        "success": False,
        "correlation_id": str(correlation_id),
        "transaction_id": None,
        "errors": []
    }
    
    try:
        # Parse event body
        if isinstance(event_body, bytes):
            raw_payload = json.loads(event_body.decode('utf-8'))
        elif isinstance(event_body, str):
            raw_payload = json.loads(event_body)
        else:
            raw_payload = event_body
        
        # Parse and validate transaction
        parser = _get_parser()
        message_body = json.dumps(raw_payload)
        parse_result: ParseResult = parser.parse_and_validate(message_body)
        
        if not parse_result.success:
            result["errors"].append(f"Validation error: {parse_result.error}")
            return result
        
        transaction: ParsedTransaction = parse_result.transaction
        result["transaction_id"] = transaction.transaction_id
        
        # 1. Store raw event to Blob Storage
        blob_path = _store_raw_event_to_blob(
            transaction=transaction,
            correlation_id=correlation_id,
            raw_payload=raw_payload
        )
        result["blob_stored"] = blob_path is not None
        
        # 2. Extract metrics
        metrics = _extract_metrics(transaction)
        
        # 3. Store dynamic metrics
        metrics_stored = _store_dynamic_metrics(
            transaction=transaction,
            correlation_id=correlation_id,
            metrics=metrics
        )
        result["metrics_stored"] = metrics_stored
        
        # 4. Update payment_metrics_5m
        payment_metrics_updated = _update_payment_metrics_5m(transaction)
        result["payment_metrics_updated"] = payment_metrics_updated
        
        # 5. Update aggregate_histograms
        histograms_updated = _update_aggregate_histograms(
            transaction=transaction,
            metrics=metrics,
            correlation_id=correlation_id
        )
        result["histograms_updated"] = histograms_updated
        
        result["success"] = True
        result["elapsed_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
        
    except Exception as e:
        result["errors"].append(f"Processing error: {str(e)}")
        result["error_traceback"] = traceback.format_exc()
        logger.error(
            f"Failed to process transaction locally: {e}",
            exc_info=True,
            extra={"correlation_id": str(correlation_id)}
        )
    
    return result

