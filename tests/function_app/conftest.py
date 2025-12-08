"""
Shared fixtures for function_app tests.
"""

import pytest
from datetime import datetime
from src.function_app.messaging import Message, MessageBatch


@pytest.fixture
def sample_message():
    """Create a sample Message for testing."""
    return Message(
        message_id="msg-123",
        correlation_id="corr-456",
        timestamp=datetime.utcnow(),
        headers={"source": "test"},
        body='{"amount": 100.0, "currency": "USD"}',
        offset=12345,
        sequence_number=67890
    )


@pytest.fixture
def sample_message_batch(sample_message):
    """Create a sample MessageBatch for testing."""
    messages = [
        sample_message,
        Message(
            message_id="msg-124",
            correlation_id="corr-457",
            timestamp=datetime.utcnow(),
            body='{"amount": 200.0, "currency": "EUR"}'
        )
    ]
    return MessageBatch(
        messages=messages,
        batch_id="batch-123",
        received_at=datetime.utcnow(),
        broker_type="event_hubs"
    )


@pytest.fixture
def sample_invalid_json_message():
    """Create a Message with invalid JSON body."""
    return Message(
        message_id="msg-invalid",
        correlation_id="corr-invalid",
        timestamp=datetime.utcnow(),
        body="not valid json {"
    )


@pytest.fixture
def sample_empty_message():
    """Create a Message with empty body."""
    return Message(
        message_id="msg-empty",
        correlation_id="corr-empty",
        timestamp=datetime.utcnow(),
        body=""
    )

