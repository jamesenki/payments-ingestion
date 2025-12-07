"""
Data parser and validation engine with schema support.

Implements WO-38: Build Data Parser and Validation Engine with Schema Support

This module provides comprehensive data parsing and validation with configurable
schema definitions, field-level validation, and dead-letter queue routing for
invalid messages.
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from threading import Lock

from .models import (
    ParsedTransaction,
    ValidationError,
    ParseResult,
    FailedMessage,
)
from .parser import TransactionParser

logger = logging.getLogger(__name__)


class DataParser:
    """
    Comprehensive data parser and validation engine.
    
    This class extends TransactionParser with additional features:
    - Configurable schema definitions
    - Hot-reloadable schemas
    - Dead-letter queue routing
    - Validation metrics tracking
    - Support for nested data structures
    
    Features:
    - JSON deserialization with error handling
    - Schema-based validation with required/optional fields
    - Field-level validation (types, ranges, patterns, business rules)
    - Dead-letter queue routing for invalid messages
    - Validation metrics tracking
    - Hot-reloadable schema definitions
    """
    
    def __init__(
        self,
        schema_manager=None,
        dead_letter_handler: Optional[Callable[[FailedMessage], None]] = None
    ):
        """
        Initialize DataParser.
        
        Args:
            schema_manager: Optional schema manager for loading schemas
            dead_letter_handler: Optional callback for routing failed messages
                                to dead-letter queue
        """
        self.parser = TransactionParser(schema_manager)
        self.schema_manager = schema_manager
        self.dead_letter_handler = dead_letter_handler
        
        # Schema cache with hot-reload support
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._schema_lock = Lock()
        self._last_schema_reload = datetime.utcnow()
        
        # Validation metrics
        self._metrics = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "failed_by_type": {},
            "total_processing_time_ms": 0.0,
        }
        self._metrics_lock = Lock()
        
        logger.info("DataParser initialized with schema support and dead-letter routing")
    
    def parse_and_validate(
        self,
        message_body: str,
        schema_name: Optional[str] = None
    ) -> ParseResult:
        """
        Parse and validate a transaction message with schema support.
        
        This method performs JSON deserialization, schema-based validation,
        and returns a ParseResult. Invalid messages are routed to dead-letter
        queue if configured.
        
        Args:
            message_body: Raw message body string (JSON)
            schema_name: Optional schema name for validation
        
        Returns:
            ParseResult with either ParsedTransaction or ValidationError
        """
        start_time = time.time()
        
        with self._metrics_lock:
            self._metrics["total_processed"] += 1
        
        try:
            # Load schema if provided
            schema = None
            if schema_name:
                schema = self._load_schema(schema_name)
            
            # Parse and validate using TransactionParser
            result = self.parser.parse_and_validate(message_body, schema_name)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            with self._metrics_lock:
                self._metrics["total_processing_time_ms"] += elapsed_ms
                
                if result.success:
                    self._metrics["successful"] += 1
                else:
                    self._metrics["failed"] += 1
                    
                    # Track failure by error type
                    if result.error:
                        error_type = result.error.constraint
                        self._metrics["failed_by_type"][error_type] = \
                            self._metrics["failed_by_type"].get(error_type, 0) + 1
                    
                    # Route to dead-letter queue
                    self._route_to_dead_letter(result, message_body)
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error in parse_and_validate: {str(e)}", exc_info=True)
            
            # Create error result
            error = ValidationError(
                field="parser",
                constraint="unexpected_error",
                expected="successful parsing",
                actual=f"error: {str(e)}",
                message=f"Unexpected error: {str(e)}"
            )
            result = ParseResult.error_result(error, message_body)
            
            # Route to dead-letter queue
            self._route_to_dead_letter(result, message_body)
            
            with self._metrics_lock:
                self._metrics["failed"] += 1
            
            return result
    
    def parse_batch(
        self,
        messages: List[str],
        schema_name: Optional[str] = None
    ) -> List[ParseResult]:
        """
        Parse and validate a batch of messages.
        
        Args:
            messages: List of raw message body strings
            schema_name: Optional schema name for validation
        
        Returns:
            List of ParseResult objects
        """
        results = []
        for message_body in messages:
            result = self.parse_and_validate(message_body, schema_name)
            results.append(result)
        return results
    
    def _load_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """
        Load schema definition with caching and hot-reload support.
        
        Args:
            schema_name: Name of the schema to load
        
        Returns:
            Schema definition dictionary, or None if not found
        """
        with self._schema_lock:
            # Check if schema is cached and still valid
            if schema_name in self._schemas:
                # For hot-reload, check if schema needs refresh
                # In production, this would check schema modification time
                return self._schemas[schema_name]
            
            # Load schema from schema manager
            if self.schema_manager:
                try:
                    schema = self.schema_manager.get_schema(schema_name)
                    if schema:
                        # Validate schema before caching
                        if self._validate_schema(schema):
                            self._schemas[schema_name] = schema
                            self._last_schema_reload = datetime.utcnow()
                            logger.debug(f"Loaded and cached schema: {schema_name}")
                            return schema
                        else:
                            logger.error(f"Invalid schema structure: {schema_name}")
                            return None
                except Exception as e:
                    logger.error(f"Failed to load schema {schema_name}: {str(e)}")
                    return None
            
            return None
    
    def _validate_schema(self, schema: Dict[str, Any]) -> bool:
        """
        Validate schema structure before applying.
        
        Args:
            schema: Schema definition to validate
        
        Returns:
            True if schema is valid, False otherwise
        """
        # Basic schema structure validation
        if not isinstance(schema, dict):
            return False
        
        # Check for required schema fields
        # This is a simplified validation - can be extended
        return True
    
    def _route_to_dead_letter(
        self,
        result: ParseResult,
        raw_message: str
    ) -> None:
        """
        Route failed message to dead-letter queue.
        
        Args:
            result: ParseResult containing error information
            raw_message: Original raw message
        """
        if not result.error:
            return
        
        if not self.dead_letter_handler:
            logger.debug("No dead-letter handler configured, skipping routing")
            return
        
        try:
            # Extract transaction/correlation ID if available
            transaction_id = None
            correlation_id = None
            
            # Try to parse message to extract IDs
            try:
                data = json.loads(raw_message)
                transaction_id = data.get("transaction_id")
                correlation_id = data.get("correlation_id")
            except (json.JSONDecodeError, AttributeError):
                pass
            
            # Create FailedMessage
            failed_message = FailedMessage(
                transaction_id=transaction_id,
                correlation_id=correlation_id,
                failure_reason=result.error.constraint,
                failure_details={
                    "field": result.error.field,
                    "expected": result.error.expected,
                    "actual": result.error.actual,
                    "message": result.error.message,
                },
                raw_message=raw_message,
                timestamp=datetime.utcnow()
            )
            
            # Route to dead-letter queue
            self.dead_letter_handler(failed_message)
            
            logger.info(
                f"Routed failed message to dead-letter queue: "
                f"transaction_id={transaction_id}, "
                f"error={result.error.constraint}"
            )
            
        except Exception as e:
            logger.error(
                f"Failed to route message to dead-letter queue: {str(e)}",
                exc_info=True
            )
    
    def reload_schemas(self) -> int:
        """
        Reload all cached schemas (hot-reload support).
        
        Returns:
            Number of schemas reloaded
        """
        with self._schema_lock:
            count = len(self._schemas)
            self._schemas.clear()
            self._last_schema_reload = datetime.utcnow()
            logger.info(f"Cleared {count} cached schemas for hot-reload")
            return count
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get validation metrics.
        
        Returns:
            Dictionary with validation metrics including:
            - total_processed: Total messages processed
            - successful: Number of successful validations
            - failed: Number of failed validations
            - failed_by_type: Breakdown of failures by error type
            - avg_processing_time_ms: Average processing time per message
            - success_rate: Percentage of successful validations
        """
        with self._metrics_lock:
            total = self._metrics["total_processed"]
            successful = self._metrics["successful"]
            failed = self._metrics["failed"]
            total_time = self._metrics["total_processing_time_ms"]
            
            avg_time = total_time / total if total > 0 else 0.0
            success_rate = (successful / total * 100) if total > 0 else 0.0
            
            return {
                "total_processed": total,
                "successful": successful,
                "failed": failed,
                "failed_by_type": dict(self._metrics["failed_by_type"]),
                "avg_processing_time_ms": avg_time,
                "success_rate": success_rate,
            }
    
    def reset_metrics(self) -> None:
        """Reset validation metrics."""
        with self._metrics_lock:
            self._metrics = {
                "total_processed": 0,
                "successful": 0,
                "failed": 0,
                "failed_by_type": {},
                "total_processing_time_ms": 0.0,
            }
            logger.info("Validation metrics reset")

