#!/bin/bash
# Script to test the simulator locally and generate transaction file

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Payment Simulator Local Test"
echo "=========================================="
echo ""

# Create output directory
OUTPUT_DIR="$PROJECT_ROOT/output"
mkdir -p "$OUTPUT_DIR"

# Configuration file
CONFIG_FILE="$PROJECT_ROOT/config/simulator_config_test.yaml"

echo "Configuration: $CONFIG_FILE"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Check if config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Run the simulator
echo "Starting simulator..."
echo ""

cd "$PROJECT_ROOT"
python3 -m src.simulator.main --config "$CONFIG_FILE"

echo ""
echo "=========================================="
echo "Simulator completed!"
echo "=========================================="
echo ""

# Check output file
OUTPUT_FILE="$OUTPUT_DIR/transactions.jsonl"
if [ -f "$OUTPUT_FILE" ]; then
    LINE_COUNT=$(wc -l < "$OUTPUT_FILE" | tr -d ' ')
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    
    echo "Output file: $OUTPUT_FILE"
    echo "Transactions generated: $LINE_COUNT"
    echo "File size: $FILE_SIZE"
    echo ""
    
    # Show first few transactions
    echo "First 3 transactions:"
    echo "----------------------------------------"
    head -n 3 "$OUTPUT_FILE" | python3 -m json.tool
    echo ""
    
    echo "✅ Test completed successfully!"
else
    echo "⚠️  Warning: Output file not found: $OUTPUT_FILE"
    exit 1
fi

