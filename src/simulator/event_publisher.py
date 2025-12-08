"""
Event publisher wrapper that integrates with WO-6 Event Hub publisher.
"""

import os
from typing import Dict, Any, List

from .publishers.event_hub import EventHubPublisher
from .publishers.base import BasePublisher


def create_publisher(config: Dict[str, Any]) -> BasePublisher:
    """
    Create appropriate publisher based on configuration.
    
    Args:
        config: Publisher configuration
        
    Returns:
        Publisher instance
    """
    destination = config.get("destination", "event_hub")
    
    if destination == "event_hub":
        # Get connection string from environment or config
        connection_string = config.get("connection_string")
        if connection_string and connection_string.startswith("${"):
            # Environment variable reference
            env_var = connection_string.strip("${}").strip()
            connection_string = os.getenv(env_var)
            if not connection_string:
                raise ValueError(f"Environment variable {env_var} not set")
        
        # Extract event hub name from connection string if not provided
        eventhub_name = config.get("eventhub_name")
        if not eventhub_name and connection_string:
            # Try to extract from EntityPath in connection string
            for part in connection_string.split(";"):
                if part.startswith("EntityPath="):
                    eventhub_name = part.split("=", 1)[1]
                    break
        
        publisher_config = {
            "connection_string": connection_string,
            "eventhub_name": eventhub_name,
            "batch_size": config.get("batch_size", 100),
            "max_retries": 3,
            "retry_delay": 1.0,
            "use_managed_identity": config.get("use_managed_identity", False),
        }
        
        return EventHubPublisher(publisher_config)
    
    elif destination == "file":
        # File publisher
        file_path = config.get("file_path", "transactions.jsonl")
        if not file_path:
            raise ValueError("file_path is required for file destination")
        
        publisher_config = {
            "file_path": file_path,
            "format": config.get("format", "jsonl"),  # jsonl or json_array
            "append": config.get("append", False),
            "batch_size": config.get("batch_size", 100),
        }
        
        from .publishers.file import FilePublisher
        return FilePublisher(publisher_config)
    
    elif destination == "stdout":
        # Stdout publisher - use file publisher with stdout
        publisher_config = {
            "file_path": "/dev/stdout" if os.name != "nt" else "CON",
            "format": "jsonl",
            "append": False,
            "batch_size": config.get("batch_size", 100),
        }
        
        from .publishers.file import FilePublisher
        return FilePublisher(publisher_config)
    
    else:
        raise ValueError(f"Unknown destination: {destination}")

