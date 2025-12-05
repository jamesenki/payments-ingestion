"""
Data extraction module for the metric engine.
"""

import os
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool

from .models import RawTransaction
from .utils.logger import get_logger


class DataExtractor:
    """Extracts transaction data from PostgreSQL."""
    
    def __init__(
        self,
        connection_string: str,
        batch_size: int = 1000,
        max_retries: int = 3,
        retry_delay_seconds: int = 5
    ):
        """
        Initialize data extractor.
        
        Args:
            connection_string: PostgreSQL connection string
            batch_size: Number of records to fetch per batch
            max_retries: Maximum number of retry attempts
            retry_delay_seconds: Delay between retries
        """
        self.connection_string = connection_string
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.logger = get_logger("metric_engine.data_extractor")
        self.connection_pool = None
    
    def _get_connection(self):
        """Get a database connection from pool or create new one."""
        if self.connection_pool is None:
            # Create connection pool
            try:
                self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                    1, 10, self.connection_string
                )
            except Exception as e:
                self.logger.error(f"Failed to create connection pool: {e}")
                raise
        
        return self.connection_pool.getconn()
    
    def _return_connection(self, conn):
        """Return connection to pool."""
        if self.connection_pool:
            self.connection_pool.putconn(conn)
    
    def extract_transactions(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[RawTransaction]:
        """
        Extract transactions from PostgreSQL.
        
        Args:
            start_time: Start timestamp filter (inclusive)
            end_time: End timestamp filter (exclusive)
            limit: Maximum number of records to fetch
            
        Returns:
            List of RawTransaction objects
        """
        for attempt in range(self.max_retries):
            try:
                conn = self._get_connection()
                try:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        query = self._build_query(start_time, end_time, limit)
                        cursor.execute(query)
                        
                        transactions = []
                        for row in cursor.fetchall():
                            transaction = self._row_to_transaction(dict(row))
                            transactions.append(transaction)
                        
                        self.logger.info(
                            f"Extracted {len(transactions)} transactions",
                            extra={"extra_fields": {
                                "start_time": start_time.isoformat() if start_time else None,
                                "end_time": end_time.isoformat() if end_time else None,
                                "count": len(transactions)
                            }}
                        )
                        
                        return transactions
                finally:
                    self._return_connection(conn)
            
            except Exception as e:
                self.logger.warning(
                    f"Extraction attempt {attempt + 1} failed: {e}",
                    exc_info=True
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay_seconds)
                else:
                    raise
        
        return []
    
    def _build_query(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        limit: Optional[int]
    ) -> str:
        """Build SQL query for transaction extraction."""
        query = "SELECT * FROM NormalizedTransactions WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND transaction_timestamp >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND transaction_timestamp < %s"
            params.append(end_time)
        
        query += " ORDER BY transaction_timestamp ASC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return query
    
    def _row_to_transaction(self, row: Dict[str, Any]) -> RawTransaction:
        """Convert database row to RawTransaction."""
        return RawTransaction(
            transaction_id=row["transaction_id"],
            transaction_timestamp=row["transaction_timestamp"],
            amount=row["amount"],
            currency=row["currency"],
            payment_method=row["payment_method"],
            payment_status=row["payment_status"],
            customer_id=row.get("customer_id"),
            customer_email=row.get("customer_email"),
            customer_country=row.get("customer_country"),
            merchant_id=row.get("merchant_id"),
            merchant_name=row.get("merchant_name"),
            merchant_category=row.get("merchant_category"),
            transaction_type=row.get("transaction_type"),
            channel=row.get("channel"),
            device_type=row.get("device_type"),
            metadata=row.get("metadata")
        )
    
    def extract_batch(
        self,
        offset: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[RawTransaction]:
        """
        Extract a batch of transactions with offset.
        
        Args:
            offset: Number of records to skip
            start_time: Start timestamp filter
            end_time: End timestamp filter
            
        Returns:
            List of RawTransaction objects
        """
        for attempt in range(self.max_retries):
            try:
                conn = self._get_connection()
                try:
                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                        query = self._build_query(start_time, end_time, None)
                        query += f" OFFSET {offset} LIMIT {self.batch_size}"
                        cursor.execute(query)
                        
                        transactions = []
                        for row in cursor.fetchall():
                            transaction = self._row_to_transaction(dict(row))
                            transactions.append(transaction)
                        
                        return transactions
                finally:
                    self._return_connection(conn)
            
            except Exception as e:
                self.logger.warning(
                    f"Batch extraction attempt {attempt + 1} failed: {e}",
                    exc_info=True
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay_seconds)
                else:
                    raise
        
        return []
    
    def close(self):
        """Close connection pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            self.connection_pool = None

