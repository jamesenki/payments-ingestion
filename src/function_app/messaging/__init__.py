"""
Message processing components for Event Hubs and Kafka integration.

This module provides foundational data structures and interfaces for
message consumption and processing.
"""

from .message import Message, MessageBatch

__all__ = [
    'Message',
    'MessageBatch',
]

