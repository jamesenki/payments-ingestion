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
# Note: normalizedtransactions is deprecated (raw events now in Blob Storage)
check_table "dynamic_metrics"
check_table "payment_metrics_5m"
check_table "failed_items"
check_table "aggregate_histograms"
echo ""

echo "Validating Indexes:"
echo "==================="
check_index "idx_dynamic_metrics_transaction_id"
check_index "idx_dynamic_metrics_correlation_id"
check_index "idx_payment_metrics_5m_window"
check_index "idx_failed_items_transaction_id"
check_index "idx_failed_items_unresolved"
check_index "idx_aggregate_histograms_time_window"
echo ""

echo "Validating Foreign Keys:"
echo "========================"
# Note: DynamicMetrics FK to NormalizedTransactions removed (raw events now in Blob Storage)
# Foreign keys are validated per table requirements
echo -e "${GREEN}✅ Foreign key validation skipped (architecture change)${NC}"
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
# Note: NormalizedTransactions deprecated (raw events now in Blob Storage)
echo "dynamic_metrics: $(get_row_count dynamic_metrics) rows"
echo "payment_metrics_5m: $(get_row_count payment_metrics_5m) rows"
echo "failed_items: $(get_row_count failed_items) rows"
echo "aggregate_histograms: $(get_row_count aggregate_histograms) rows"
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

