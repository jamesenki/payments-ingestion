"""
Base publisher interface for transaction data.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime


class BasePublisher(ABC):
    """
    Abstract base class for transaction publishers.
    
    All publishers must implement:
    - publish() - Publish a single transaction
    - publish_batch() - Publish multiple transactions
    - close() - Clean up resources
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the publisher.
        
        Args:
            config: Publisher-specific configuration
        """
        self.config = config
        self.batch: List[Dict[str, Any]] = []
        self.batch_size = config.get("batch_size", 100)
        self.metrics = None  # Will be set by implementing class
    
    @abstractmethod
    async def publish(self, transaction: Dict[str, Any]) -> bool:
        """
        Publish a single transaction.
        
        Args:
            transaction: Transaction data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def publish_batch(self, transactions: List[Dict[str, Any]]) -> int:
        """
        Publish a batch of transactions.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Number of successfully published transactions
        """
        pass
    
    def add_to_batch(self, transaction: Dict[str, Any]) -> bool:
        """
        Add transaction to batch. Auto-publishes when batch is full.
        
        Args:
            transaction: Transaction data dictionary
            
        Returns:
            True if added to batch, False if batch was published
        """
        self.batch.append(transaction)
        
        if len(self.batch) >= self.batch_size:
            # Batch is full, publish it
            return False
        
        return True
    
    async def flush_batch(self) -> int:
        """
        Publish any remaining transactions in the batch.
        
        Returns:
            Number of transactions published
        """
        if not self.batch:
            return 0
        
        count = await self.publish_batch(self.batch)
        self.batch.clear()
        return count
    
    @abstractmethod
    async def close(self):
        """Close the publisher and clean up resources."""
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Sync close for compatibility
        pass
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        await self.flush_batch()

