"""
Comprehensive unit tests for event_publisher factory to increase coverage.
"""

import pytest
import os
from unittest.mock import patch

from simulator.event_publisher import create_publisher


class TestEventPublisherComprehensive:
    """Comprehensive tests for event_publisher factory."""
    
    def test_create_publisher_with_connection_string_in_config(self):
        """Test creating publisher with connection string in config."""
        config = {
            "destination": "event_hub",
            "batch_size": 100,
            "connection_string": "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test;EntityPath=test",
        }
        
        with patch('simulator.publishers.event_hub.AZURE_EVENTHUB_AVAILABLE', True):
            try:
                publisher = create_publisher(config)
                assert publisher is not None
            except ImportError:
                pytest.skip("Azure SDK not available")
    
    def test_create_publisher_with_env_var_reference(self):
        """Test creating publisher with environment variable reference."""
        os.environ["TEST_EVENTHUB_CONN"] = "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test;EntityPath=test"
        
        config = {
            "destination": "event_hub",
            "batch_size": 100,
            "connection_string": "${TEST_EVENTHUB_CONN}",
        }
        
        with patch('simulator.publishers.event_hub.AZURE_EVENTHUB_AVAILABLE', True):
            try:
                publisher = create_publisher(config)
                assert publisher is not None
            except ImportError:
                pytest.skip("Azure SDK not available")
            finally:
                if "TEST_EVENTHUB_CONN" in os.environ:
                    del os.environ["TEST_EVENTHUB_CONN"]
    
    def test_create_publisher_extracts_eventhub_name(self):
        """Test that publisher extracts eventhub name from connection string."""
        config = {
            "destination": "event_hub",
            "batch_size": 100,
            "connection_string": "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test;EntityPath=my-hub",
        }
        
        with patch('simulator.publishers.event_hub.AZURE_EVENTHUB_AVAILABLE', True):
            try:
                publisher = create_publisher(config)
                assert publisher is not None
                # Should have extracted eventhub name
                assert publisher.config.get("eventhub_name") == "my-hub" or publisher.eventhub_name == "my-hub"
            except ImportError:
                pytest.skip("Azure SDK not available")
    
    def test_create_publisher_file_destination(self):
        """Test creating publisher with file destination."""
        config = {
            "destination": "file",
            "batch_size": 100,
        }
        
        with pytest.raises(NotImplementedError):
            create_publisher(config)
    
    def test_create_publisher_stdout_destination(self):
        """Test creating publisher with stdout destination."""
        config = {
            "destination": "stdout",
            "batch_size": 100,
        }
        
        with pytest.raises(NotImplementedError):
            create_publisher(config)
    
    def test_create_publisher_default_destination(self):
        """Test creating publisher with default destination."""
        import os
        conn_str = os.getenv("EVENTHUB_CONNECTION_STRING", "")
        config = {
            "batch_size": 100,
            "connection_string": conn_str or "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test;EntityPath=test",
        }
        
        with patch('simulator.publishers.event_hub.AZURE_EVENTHUB_AVAILABLE', True):
            try:
                publisher = create_publisher(config)
                assert publisher is not None
            except ImportError:
                pytest.skip("Azure SDK not available")

