#!/bin/bash
# Run all simulator tests

set -e

echo "============================================================"
echo "RUNNING ALL SIMULATOR TESTS"
echo "============================================================"
echo ""

echo "1. Basic Functional Tests..."
python3 tests/test_simulator_basic.py
echo ""

echo "2. Integration Tests..."
python3 tests/test_integration.py
echo ""

echo "============================================================"
echo "✅ ALL TESTS COMPLETE"
echo "============================================================"
