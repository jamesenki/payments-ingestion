"""
File publisher for writing transactions to a local file.

This publisher writes transactions to a JSON file, one transaction per line (JSONL format)
or as a JSON array, depending on configuration.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import asyncio

from .base import BasePublisher
from .metrics import PublisherMetrics

logger = logging.getLogger(__name__)


class FilePublisher(BasePublisher):
    """
    Publisher that writes transactions to a local file.
    
    Supports:
    - JSONL format (one JSON object per line) - default
    - JSON array format
    - Automatic file rotation
    - Append mode for multiple runs
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize FilePublisher.
        
        Args:
            config: Publisher configuration with:
                - file_path: Path to output file (required)
                - format: "jsonl" (default) or "json_array"
                - append: If True, append to existing file (default: False)
        """
        super().__init__(config)
        self.file_path = Path(config.get("file_path", "transactions.jsonl"))
        self.format = config.get("format", "jsonl")  # jsonl or json_array
        self.append = config.get("append", False)
        
        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # For JSON array format, we need to track if file exists
        self.file_exists = self.file_path.exists()
        self.transactions_buffer: List[Dict[str, Any]] = []
        self._file_opened = False  # Track if file has been opened in this session
        
        # Initialize metrics
        self.metrics = PublisherMetrics()
        
        logger.info(f"FilePublisher initialized: {self.file_path}, format={self.format}")
    
    def _write_jsonl(self, transactions: List[Dict[str, Any]]) -> None:
        """Write transactions in JSONL format (one per line)."""
        # If append is False but file was already opened in this session, append to it
        # Otherwise, use write mode only for the first write
        if self.append or self._file_opened:
            mode = "a"
        else:
            mode = "w"
            self._file_opened = True
        
        with open(self.file_path, mode=mode, encoding="utf-8") as f:
            for transaction in transactions:
                json_line = json.dumps(transaction, default=str) + "\n"
                f.write(json_line)
    
    def _write_json_array(self, transactions: List[Dict[str, Any]]) -> None:
        """Write transactions as JSON array."""
        # If file exists and we're appending, we need to handle the array format
        if self.file_exists and self.append:
            # Read existing content, append, and rewrite
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
                existing_data = json.loads(content) if content.strip() else []
            
            existing_data.extend(transactions)
            
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(existing_data, indent=2, default=str))
        else:
            # New file or overwrite mode
            # If file was already opened in this session, append to it
            if self._file_opened:
                mode = "a"
            else:
                mode = "w"
                self._file_opened = True
            
            with open(self.file_path, mode=mode, encoding="utf-8") as f:
                if not self.file_exists or mode == "w":
                    # Start new array
                    f.write("[\n")
                    self.file_exists = True
                
                # Write transactions
                for i, transaction in enumerate(transactions):
                    if i > 0 or self._file_opened:
                        f.write(",\n")
                    
                    json_str = json.dumps(transaction, indent=2, default=str)
                    # Indent each line
                    indented = "\n".join("  " + line for line in json_str.split("\n"))
                    f.write(indented)
    
    async def publish(self, transaction: Dict[str, Any]) -> bool:
        """
        Publish a single transaction to file.
        
        Args:
            transaction: Transaction data dictionary
            
        Returns:
            True if successful
        """
        return await self.publish_batch([transaction]) == 1
    
    async def publish_batch(self, transactions: List[Dict[str, Any]]) -> int:
        """
        Publish a batch of transactions to file.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Number of successfully published transactions
        """
        if not transactions:
            return 0
        
        start_time = datetime.utcnow()
        
        try:
            # Run file I/O in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            if self.format == "jsonl":
                await loop.run_in_executor(None, self._write_jsonl, transactions)
            elif self.format == "json_array":
                await loop.run_in_executor(None, self._write_json_array, transactions)
            else:
                raise ValueError(f"Unknown format: {self.format}")
            
            # Record success
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.metrics.record_success(count=len(transactions), latency_ms=latency_ms)
            
            logger.debug(f"Wrote {len(transactions)} transactions to {self.file_path}")
            return len(transactions)
            
        except Exception as e:
            logger.error(f"Error writing to file: {str(e)}", exc_info=True)
            self.metrics.record_failure(count=len(transactions))
            return 0
    
    async def close(self):
        """Close the file and finalize JSON array if needed."""
        # If JSON array format and file exists, ensure it's properly closed
        if self.format == "json_array" and self.file_path.exists():
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._finalize_json_array)
            except Exception as e:
                logger.warning(f"Error finalizing JSON array: {str(e)}")
        
        logger.info(f"File publisher closed: {self.file_path}")
    
    def _finalize_json_array(self):
        """Finalize JSON array by ensuring closing bracket."""
        with open(self.file_path, "r+", encoding="utf-8") as f:
            content = f.read()
            if not content.strip().endswith("]"):
                f.seek(0, 2)  # Seek to end
                if not content.strip().endswith("\n"):
                    f.write("\n")
                f.write("]")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get publisher metrics."""
        return self.metrics.get_summary()

