"""
Azure Function application for payment transaction processing.

This package contains the Azure Function entry point and supporting modules
for processing payment transactions from Event Hubs.

Main Entry Point:
    - run.py: Azure Function entry point with Event Hub trigger
    - local_test_runner.py: Local testing without Azure Functions runtime

Modules:
    - consumer: Message consumer implementations (Event Hubs, Kafka)
    - parsing: Transaction parsing and validation
    - storage: Blob Storage and Parquet serialization
    - connections: Database and storage connection management
    - messaging: Message and MessageBatch data structures
"""

# Import main function for Azure Functions runtime
from .run import process_payment_transactions

__all__ = ["process_payment_transactions"]

