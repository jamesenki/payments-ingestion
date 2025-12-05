#!/bin/bash
#
# Database Schema Validation Script
# Validates that all required tables, indexes, and constraints exist
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Database Schema Validation"
echo "========================================"
echo ""

# Check required environment variables
if [ -z "$DATABASE_HOST" ] || [ -z "$DATABASE_NAME" ] || [ -z "$DATABASE_USER" ] || [ -z "$DATABASE_PASSWORD" ]; then
    echo -e "${RED}❌ Required environment variables are not set${NC}"
    exit 1
fi

# Build connection string
export PGPASSWORD="$DATABASE_PASSWORD"
PSQL_CMD="psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME -t -A"

VALIDATION_PASSED=true

# Function to check if table exists
check_table() {
    local table_name=$1
    echo -n "Checking table '$table_name'... "
    
    local result=$($PSQL_CMD -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='${table_name,,}';")
    
    if [ "$result" -eq 1 ]; then
        echo -e "${GREEN}✅ EXISTS${NC}"
        return 0
    else
        echo -e "${RED}❌ MISSING${NC}"
        VALIDATION_PASSED=false
        return 1
    fi
}

# Function to check if index exists
check_index() {
    local index_name=$1
    echo -n "Checking index '$index_name'... "
    
    local result=$($PSQL_CMD -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname='public' AND indexname='$index_name';")
    
    if [ "$result" -eq 1 ]; then
        echo -e "${GREEN}✅ EXISTS${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  MISSING${NC}"
        # Indexes are warnings, not failures
        return 0
    fi
}

# Function to get table row count
get_row_count() {
    local table_name=$1
    local count=$($PSQL_CMD -c "SELECT COUNT(*) FROM $table_name;" 2>/dev/null || echo "0")
    echo $count
}

echo "Validating Required Tables:"
echo "============================"
check_table "normalizedtransactions"
check_table "dynamicmetrics"
check_table "payment_metrics_5m"
echo ""

echo "Validating Indexes:"
echo "==================="
check_index "idx_normalized_transactions_timestamp"
check_index "idx_dynamic_metrics_transaction"
check_index "idx_payment_metrics_5m_window"
echo ""

echo "Validating Foreign Keys:"
echo "========================"
echo -n "Checking DynamicMetrics -> NormalizedTransactions FK... "
FK_COUNT=$($PSQL_CMD -c "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_type='FOREIGN KEY' AND table_name='dynamicmetrics';")
if [ "$FK_COUNT" -ge 1 ]; then
    echo -e "${GREEN}✅ EXISTS${NC}"
else
    echo -e "${RED}❌ MISSING${NC}"
    VALIDATION_PASSED=false
fi
echo ""

echo "Validating Views:"
echo "================="
echo -n "Checking view 'payment_metrics_hourly'... "
VIEW_COUNT=$($PSQL_CMD -c "SELECT COUNT(*) FROM information_schema.views WHERE table_schema='public' AND table_name='payment_metrics_hourly';")
if [ "$VIEW_COUNT" -eq 1 ]; then
    echo -e "${GREEN}✅ EXISTS${NC}"
else
    echo -e "${YELLOW}⚠️  MISSING${NC}"
fi

echo -n "Checking view 'payment_metrics_daily'... "
VIEW_COUNT=$($PSQL_CMD -c "SELECT COUNT(*) FROM information_schema.views WHERE table_schema='public' AND table_name='payment_metrics_daily';")
if [ "$VIEW_COUNT" -eq 1 ]; then
    echo -e "${GREEN}✅ EXISTS${NC}"
else
    echo -e "${YELLOW}⚠️  MISSING${NC}"
fi
echo ""

echo "Table Statistics:"
echo "================="
echo "NormalizedTransactions: $(get_row_count normalizedtransactions) rows"
echo "DynamicMetrics: $(get_row_count dynamicmetrics) rows"
echo "payment_metrics_5m: $(get_row_count payment_metrics_5m) rows"
echo ""

echo "========================================"
if [ "$VALIDATION_PASSED" = "true" ]; then
    echo -e "${GREEN}✅ All validations passed!${NC}"
    echo "========================================"
    exit 0
else
    echo -e "${RED}❌ Validation failed!${NC}"
    echo "========================================"
    exit 1
fi

# Clean up
unset PGPASSWORD

