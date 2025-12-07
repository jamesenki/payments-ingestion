"""
Message consumer components for Event Hubs and Kafka integration.

This module provides the abstract base class and interfaces for consuming
messages from different broker types (Event Hubs, Kafka).
"""

from .base import MessageConsumer

__all__ = [
    'MessageConsumer',
]

