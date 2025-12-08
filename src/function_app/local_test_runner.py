"""
Local test runner for Azure Function without Azure Functions runtime.

This module provides a way to test the Azure Function locally without requiring
the Azure Functions Core Tools or Azure Functions runtime.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.function_app.run import process_transaction_local, _get_connection_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_transaction(file_path: str) -> Dict[str, Any]:
    """
    Load a test transaction from a JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Transaction dictionary
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def run_local_test(
    transaction_data: Dict[str, Any],
    postgres_conn_str: Optional[str] = None,
    blob_conn_str: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a local test of the Azure Function.
    
    Args:
        transaction_data: Transaction data dictionary
        postgres_conn_str: PostgreSQL connection string (optional, uses env var if not provided)
        blob_conn_str: Blob Storage connection string (optional, uses env var if not provided)
        
    Returns:
        Processing result dictionary
    """
    # Set environment variables if provided
    if postgres_conn_str:
        os.environ["POSTGRES_CONNECTION_STRING"] = postgres_conn_str
    if blob_conn_str:
        os.environ["BLOB_STORAGE_CONNECTION_STRING"] = blob_conn_str
    
    # Set defaults if not in environment
    if "POSTGRES_CONNECTION_STRING" not in os.environ:
        os.environ["POSTGRES_CONNECTION_STRING"] = os.getenv(
            "AzureWebJobsStorage", "postgresql://user:pass@localhost:5432/payments_db"
        )
    if "BLOB_STORAGE_CONNECTION_STRING" not in os.environ:
        os.environ["BLOB_STORAGE_CONNECTION_STRING"] = os.getenv(
            "AzureWebJobsStorage", "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net"
        )
    
    # Process transaction
    logger.info(f"Processing transaction: {transaction_data.get('transaction_id', 'unknown')}")
    result = process_transaction_local(transaction_data)
    
    return result


def main():
    """Main entry point for local testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Local test runner for Azure Function")
    parser.add_argument(
        "--transaction-file",
        type=str,
        help="Path to JSON file containing transaction data"
    )
    parser.add_argument(
        "--transaction-json",
        type=str,
        help="Transaction data as JSON string"
    )
    parser.add_argument(
        "--postgres-conn-str",
        type=str,
        help="PostgreSQL connection string"
    )
    parser.add_argument(
        "--blob-conn-str",
        type=str,
        help="Blob Storage connection string"
    )
    
    args = parser.parse_args()
    
    # Load transaction data
    if args.transaction_file:
        transaction_data = load_test_transaction(args.transaction_file)
    elif args.transaction_json:
        transaction_data = json.loads(args.transaction_json)
    else:
        # Use sample transaction from simulator output
        sample_file = Path(__file__).parent.parent.parent / "output" / "transactions.jsonl"
        if sample_file.exists():
            logger.info(f"Using sample transaction from {sample_file}")
            with open(sample_file, 'r') as f:
                first_line = f.readline()
                transaction_data = json.loads(first_line)
        else:
            logger.error("No transaction data provided. Use --transaction-file or --transaction-json")
            sys.exit(1)
    
    # Run test
    result = run_local_test(
        transaction_data=transaction_data,
        postgres_conn_str=args.postgres_conn_str,
        blob_conn_str=args.blob_conn_str
    )
    
    # Print results
    print("\n" + "="*60)
    print("Local Test Results")
    print("="*60)
    print(json.dumps(result, indent=2, default=str))
    print("="*60)
    
    if result["success"]:
        print("\n✅ Transaction processed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Transaction processing failed!")
        if result.get("errors"):
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

