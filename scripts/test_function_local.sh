#!/bin/bash
# Local test script for Azure Function

set -e

echo "============================================================"
echo "Azure Function Local Test"
echo "============================================================"

# Check if transaction file exists
TRANSACTION_FILE="output/transactions.jsonl"
if [ ! -f "$TRANSACTION_FILE" ]; then
    echo "Error: Transaction file not found: $TRANSACTION_FILE"
    echo "Please run the simulator first to generate test data."
    exit 1
fi

# Extract first transaction
FIRST_TRANSACTION=$(head -n 1 "$TRANSACTION_FILE")

echo "Using transaction from: $TRANSACTION_FILE"
echo ""

# Run local test runner
python3 -m src.function_app.local_test_runner \
    --transaction-json "$FIRST_TRANSACTION" \
    --postgres-conn-str "${POSTGRES_CONNECTION_STRING:-postgresql://user:pass@localhost:5432/payments_db}" \
    --blob-conn-str "${BLOB_STORAGE_CONNECTION_STRING:-DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net}"

echo ""
echo "✅ Test completed!"

