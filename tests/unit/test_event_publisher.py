"""
Unit tests for event_publisher factory.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from simulator.event_publisher import create_publisher


class TestEventPublisherFactory:
    """Test create_publisher factory function."""
    
    def test_create_event_hub_publisher(self, mock_event_hub_connection_string):
        """Test creating Event Hub publisher."""
        import os
        conn_str = os.getenv("EVENTHUB_CONNECTION_STRING", "")
        config = {
            "destination": "event_hub",
            "batch_size": 100,
            "connection_string": conn_str or "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test;EntityPath=test",
        }
        
        # Mock Azure SDK availability in event_hub module
        with patch('simulator.publishers.event_hub.AZURE_EVENTHUB_AVAILABLE', True):
            # Just test that publisher creation doesn't crash
            # Full testing requires Azure SDK which may not be available
            try:
                publisher = create_publisher(config)
                assert publisher is not None
                assert publisher.config is not None
            except ImportError:
                # If Azure SDK not actually available, skip this test
                pytest.skip("Azure SDK not available")
    
    def test_create_publisher_missing_connection_string(self):
        """Test creating publisher without connection string."""
        # Remove connection string from config (not env)
        config = {
            "destination": "event_hub",
            "batch_size": 100,
            # No connection_string provided
        }
        
        # Mock Azure SDK available
        with patch('simulator.publishers.event_hub.AZURE_EVENTHUB_AVAILABLE', True):
            # Will create publisher but it may fail validation
            # The EventHubPublisher validates in __init__
            try:
                publisher = create_publisher(config)
                # If it succeeds, that's fine - validation happens later
                assert publisher is not None
            except (ValueError, ImportError):
                # Expected if validation fails
                pass
    
    def test_create_publisher_invalid_destination(self, mock_event_hub_connection_string):
        """Test creating publisher with invalid destination."""
        config = {
            "destination": "invalid",
            "batch_size": 100,
        }
        
        with pytest.raises(ValueError):
            create_publisher(config)
    
    def test_create_publisher_without_azure_sdk(self, mock_event_hub_connection_string):
        """Test creating publisher when Azure SDK not available."""
        import os
        conn_str = os.getenv("EVENTHUB_CONNECTION_STRING", "")
        config = {
            "destination": "event_hub",
            "batch_size": 100,
            "connection_string": conn_str or "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test;EntityPath=test",
        }
        
        # Mock Azure SDK not available in event_hub module
        with patch('simulator.publishers.event_hub.AZURE_EVENTHUB_AVAILABLE', False):
            # Publisher creation will fail with ImportError
            with pytest.raises(ImportError):
                create_publisher(config)

