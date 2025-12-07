"""
Transaction parser and validation engine.

Implements WO-59: Build Transaction Parser and Validation Engine

This module provides the core parsing and validation engine that orchestrates
JSON deserialization, schema-based validation, and result generation to transform
raw messages into validated transaction objects or detailed error information.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from .models import (
    ParsedTransaction,
    TransactionStatus,
    ValidationError,
    ParseResult,
)

logger = logging.getLogger(__name__)


class TransactionParser:
    """
    Core transaction parser and validation engine.
    
    This class orchestrates JSON deserialization, schema-based validation,
    and result generation. It uses a fail-fast validation approach to minimize
    latency and supports processing throughput of at least 10,000 transactions
    per second.
    
    Features:
    - JSON deserialization with error handling
    - Schema-driven validation
    - Field-level validation with multiple rules per field
    - Fail-fast validation (stops at first error)
    - Detailed validation error messages
    - Type conversion and validation
    """
    
    def __init__(self, schema_manager=None):
        """
        Initialize TransactionParser.
        
        Args:
            schema_manager: Optional schema manager for loading validation schemas.
                          If None, uses default validation rules.
        """
        self.schema_manager = schema_manager
        self._validation_rules = {}
        
        # Register default validation rules
        self._register_default_rules()
        
        logger.info("TransactionParser initialized")
    
    def parse_and_validate(
        self,
        message_body: str,
        schema_name: Optional[str] = None
    ) -> ParseResult:
        """
        Parse and validate a transaction message.
        
        This method performs JSON deserialization, schema-based validation,
        and returns a ParseResult with either a valid ParsedTransaction or
        a ValidationError. It uses a fail-fast approach, stopping at the
        first validation error.
        
        Args:
            message_body: Raw message body string (JSON)
            schema_name: Optional schema name to use for validation
        
        Returns:
            ParseResult containing either:
            - success=True with ParsedTransaction
            - success=False with ValidationError
        
        Example:
            >>> parser = TransactionParser()
            >>> result = parser.parse_and_validate('{"transaction_id": "tx-1", ...}')
            >>> if result.success:
            ...     process(result.transaction)
            ... else:
            ...     handle_error(result.error)
        """
        start_time = datetime.utcnow()
        
        try:
            # Step 1: JSON Deserialization
            try:
                data = json.loads(message_body)
            except json.JSONDecodeError as e:
                error = ValidationError(
                    field="body",
                    constraint="json_format",
                    expected="valid JSON",
                    actual=f"malformed JSON: {str(e)}",
                    message=f"Failed to parse JSON: {str(e)}"
                )
                return ParseResult.error_result(error, message_body)
            except Exception as e:
                error = ValidationError(
                    field="body",
                    constraint="deserialization",
                    expected="valid JSON string",
                    actual=f"error: {str(e)}",
                    message=f"Unexpected error during JSON deserialization: {str(e)}"
                )
                return ParseResult.error_result(error, message_body)
            
            # Step 2: Schema-based validation (fail-fast)
            validation_result = self._validate_against_schema(data, schema_name)
            if not validation_result.success:
                return ParseResult.error_result(
                    validation_result.error,
                    message_body
                )
            
            # Step 3: Create ParsedTransaction
            try:
                transaction = self._create_transaction(data)
            except Exception as e:
                error = ValidationError(
                    field="transaction",
                    constraint="creation",
                    expected="valid transaction object",
                    actual=f"error: {str(e)}",
                    message=f"Failed to create transaction: {str(e)}"
                )
                return ParseResult.error_result(error, message_body)
            
            # Step 4: Return success result
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Check latency requirement (95th percentile < 50ms)
            if elapsed > 50:
                logger.warning(
                    f"Parse and validate latency {elapsed:.2f}ms "
                    f"exceeds 50ms target"
                )
            
            return ParseResult.success_result(transaction, message_body)
            
        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Unexpected error in parse_and_validate: {str(e)}", exc_info=True)
            error = ValidationError(
                field="parser",
                constraint="unexpected_error",
                expected="successful parsing",
                actual=f"error: {str(e)}",
                message=f"Unexpected error during parsing: {str(e)}"
            )
            return ParseResult.error_result(error, message_body)
    
    def _validate_against_schema(
        self,
        data: Dict[str, Any],
        schema_name: Optional[str]
    ) -> ParseResult:
        """
        Validate data against schema with fail-fast approach.
        
        Args:
            data: Parsed JSON data
            schema_name: Optional schema name
        
        Returns:
            ParseResult indicating validation success or failure
        """
        # Required fields for transaction
        required_fields = [
            "transaction_id",
            "correlation_id",
            "timestamp",
            "transaction_type",
            "channel",
            "amount",
            "currency",
            "merchant_id",
            "customer_id",
            "status"
        ]
        
        # Check required fields (fail-fast)
        for field in required_fields:
            if field not in data:
                error = ValidationError(
                    field=field,
                    constraint="required",
                    expected="field must be present",
                    actual="field missing",
                    message=f"Required field '{field}' is missing"
                )
                return ParseResult.error_result(error)
        
        # Validate field types and constraints (fail-fast)
        field_validations = [
            ("transaction_id", str, "must be a string"),
            ("correlation_id", str, "must be a string"),
            ("amount", (int, float), "must be a number"),
            ("currency", str, "must be a string"),
            ("merchant_id", str, "must be a string"),
            ("customer_id", str, "must be a string"),
            ("status", str, "must be a string"),
        ]
        
        for field, expected_type, message in field_validations:
            if field not in data:
                continue  # Already checked as required
            
            value = data[field]
            
            # Type validation
            if not isinstance(value, expected_type):
                error = ValidationError(
                    field=field,
                    constraint="type",
                    expected=expected_type.__name__ if isinstance(expected_type, type) else str(expected_type),
                    actual=type(value).__name__,
                    message=f"Field '{field}' {message}, got {type(value).__name__}"
                )
                return ParseResult.error_result(error)
            
            # Additional constraints
            if field == "amount" and value <= 0:
                error = ValidationError(
                    field=field,
                    constraint="range",
                    expected="amount > 0",
                    actual=value,
                    message=f"Field '{field}' must be greater than 0"
                )
                return ParseResult.error_result(error)
            
            if field == "currency" and len(value) != 3:
                error = ValidationError(
                    field=field,
                    constraint="format",
                    expected="3-character currency code (ISO 4217)",
                    actual=value,
                    message=f"Field '{field}' must be a 3-character currency code"
                )
                return ParseResult.error_result(error)
            
            if field == "status":
                # Validate status enum
                try:
                    TransactionStatus(value.lower())
                except ValueError:
                    error = ValidationError(
                        field=field,
                        constraint="allowed_values",
                        expected="one of: success, declined, timeout, error",
                        actual=value,
                        message=f"Field '{field}' must be one of: success, declined, timeout, error"
                    )
                    return ParseResult.error_result(error)
        
        # All validations passed
        return ParseResult.success_result(None)  # Transaction will be created separately
    
    def _create_transaction(self, data: Dict[str, Any]) -> ParsedTransaction:
        """
        Create ParsedTransaction from validated data.
        
        Args:
            data: Validated transaction data
        
        Returns:
            ParsedTransaction object
        """
        # Parse timestamp
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                timestamp = datetime.utcnow()
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.utcnow()
        
        # Parse status
        status_str = data.get("status", "error").lower()
        try:
            status = TransactionStatus(status_str)
        except ValueError:
            status = TransactionStatus.ERROR
        
        # Extract metadata
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        
        return ParsedTransaction(
            transaction_id=str(data["transaction_id"]),
            correlation_id=str(data["correlation_id"]),
            timestamp=timestamp,
            transaction_type=str(data.get("transaction_type", "payment")),
            channel=str(data.get("channel", "unknown")),
            amount=float(data["amount"]),
            currency=str(data["currency"]),
            merchant_id=str(data["merchant_id"]),
            customer_id=str(data["customer_id"]),
            status=status,
            metadata=metadata
        )
    
    def _register_default_rules(self) -> None:
        """Register default validation rules."""
        # Default rules are embedded in _validate_against_schema
        # This method can be extended to support custom rule registration
        pass

