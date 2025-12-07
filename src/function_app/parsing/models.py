"""
Core data models for transaction parsing and validation.

Implements WO-35: Core Data Models for Transaction Parsing

This module provides the foundational data structures needed for transaction
parsing and validation, enabling the system to represent parsed transactions,
validation errors, and parse results in a consistent, type-safe manner.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class TransactionStatus(Enum):
    """
    Enumeration of possible transaction statuses.
    
    This enum represents the various states a payment transaction can be in,
    which is critical for business logic, reporting, and error handling.
    
    Values:
        SUCCESS: Transaction completed successfully
        DECLINED: Transaction was declined (e.g., insufficient funds, fraud)
        TIMEOUT: Transaction timed out before completion
        ERROR: Transaction failed due to an error
    """
    
    SUCCESS = "success"
    DECLINED = "declined"
    TIMEOUT = "timeout"
    ERROR = "error"
    
    def __str__(self) -> str:
        """Return the string value of the status."""
        return self.value


@dataclass
class ParsedTransaction:
    """
    Represents a successfully parsed payment transaction.
    
    This data model contains all the essential fields extracted from a
    raw transaction message after parsing and validation. It provides
    a structured, type-safe representation of transaction data.
    
    Attributes:
        transaction_id: Unique identifier for the transaction
        correlation_id: Correlation ID for request tracing
        timestamp: Timestamp when the transaction occurred
        transaction_type: Type of transaction (e.g., "payment", "refund")
        channel: Channel through which transaction was processed
        amount: Transaction amount as float
        currency: Currency code (ISO 4217, e.g., "USD", "EUR")
        merchant_id: Identifier for the merchant
        customer_id: Identifier for the customer
        status: Transaction status (from TransactionStatus enum)
        metadata: Additional transaction metadata as dictionary
    """
    
    transaction_id: str
    correlation_id: str
    timestamp: datetime
    transaction_type: str
    channel: str
    amount: float
    currency: str
    merchant_id: str
    customer_id: str
    status: TransactionStatus
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ParsedTransaction to dictionary representation.
        
        This method is useful for serialization, storage, and logging.
        The status enum is converted to its string value.
        
        Returns:
            Dictionary representation of the transaction
            
        Example:
            >>> tx = ParsedTransaction(...)
            >>> data = tx.to_dict()
            >>> data["status"]  # "success", "declined", etc.
        """
        return {
            "transaction_id": self.transaction_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "transaction_type": self.transaction_type,
            "channel": self.channel,
            "amount": self.amount,
            "currency": self.currency,
            "merchant_id": self.merchant_id,
            "customer_id": self.customer_id,
            "status": str(self.status.value),
            "metadata": self.metadata,
        }


@dataclass
class ValidationError:
    """
    Represents a validation error that occurred during transaction parsing.
    
    This data model captures detailed information about validation failures,
    including which field failed, what constraint was violated, and the
    expected vs actual values. This enables precise error reporting and
    debugging.
    
    Attributes:
        field: Name of the field that failed validation
        constraint: Type of constraint that was violated (e.g., "required", "type", "range")
        expected: Expected value or constraint description
        actual: Actual value that caused the failure
        message: Human-readable error message
    """
    
    field: str
    constraint: str
    expected: Any
    actual: Any
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ValidationError to dictionary representation.
        
        Returns:
            Dictionary representation of the validation error
        """
        return {
            "field": self.field,
            "constraint": self.constraint,
            "expected": self.expected,
            "actual": self.actual,
            "message": self.message,
        }


@dataclass
class ParseResult:
    """
    Represents the result of parsing a transaction message.
    
    This data model encapsulates both success and failure cases, allowing
    the parser to return a consistent structure regardless of outcome.
    It includes the parsed transaction on success, or validation errors
    on failure.
    
    Attributes:
        success: Boolean indicating whether parsing was successful
        transaction: ParsedTransaction if parsing succeeded, None otherwise
        error: ValidationError if parsing failed, None otherwise
        raw_message: Original raw message string (for debugging/replay)
    """
    
    success: bool
    transaction: Optional[ParsedTransaction] = None
    error: Optional[ValidationError] = None
    raw_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ParseResult to dictionary representation.
        
        Returns:
            Dictionary representation of the parse result
        """
        result = {
            "success": self.success,
            "raw_message": self.raw_message,
        }
        
        if self.transaction:
            result["transaction"] = self.transaction.to_dict()
        
        if self.error:
            result["error"] = self.error.to_dict()
        
        return result
    
    @classmethod
    def success_result(
        cls,
        transaction: ParsedTransaction,
        raw_message: Optional[str] = None
    ) -> 'ParseResult':
        """
        Create a successful ParseResult.
        
        Args:
            transaction: Successfully parsed transaction
            raw_message: Original raw message (optional)
            
        Returns:
            ParseResult with success=True
        """
        return cls(
            success=True,
            transaction=transaction,
            raw_message=raw_message
        )
    
    @classmethod
    def error_result(
        cls,
        error: ValidationError,
        raw_message: Optional[str] = None
    ) -> 'ParseResult':
        """
        Create a failed ParseResult.
        
        Args:
            error: Validation error that occurred
            raw_message: Original raw message (optional)
            
        Returns:
            ParseResult with success=False
        """
        return cls(
            success=False,
            error=error,
            raw_message=raw_message
        )


@dataclass
class FailedMessage:
    """
    Represents a message that failed to be processed.
    
    This data model is used for dead-letter queue storage and error
    reporting. It captures all relevant information about a failed
    message, including the failure reason and details, to enable
    investigation and potential replay.
    
    Attributes:
        transaction_id: Transaction ID if available, None otherwise
        correlation_id: Correlation ID if available, None otherwise
        failure_reason: High-level reason for failure (e.g., "parse_error", "validation_error")
        failure_details: Dictionary with detailed failure information
        raw_message: Original raw message that failed
        timestamp: Timestamp when the failure occurred
    """
    
    failure_reason: str
    raw_message: str
    timestamp: datetime
    transaction_id: Optional[str] = None
    correlation_id: Optional[str] = None
    failure_details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert FailedMessage to dictionary representation.
        
        This is useful for storing failed messages in databases or
        dead-letter queues, and for logging/auditing purposes.
        
        Returns:
            Dictionary representation of the failed message
        """
        return {
            "transaction_id": self.transaction_id,
            "correlation_id": self.correlation_id,
            "failure_reason": self.failure_reason,
            "failure_details": self.failure_details,
            "raw_message": self.raw_message,
            "timestamp": self.timestamp.isoformat(),
        }

