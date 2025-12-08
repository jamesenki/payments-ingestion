#!/bin/bash
#
# Database Schema Deployment Script
# Applies schema changes to PostgreSQL database
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SCHEMA_DIR="$PROJECT_ROOT/database/schemas"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-"dev"}
DRY_RUN=${DRY_RUN:-"false"}

echo "========================================"
echo "Database Schema Deployment"
echo "Environment: $ENVIRONMENT"
echo "Dry Run: $DRY_RUN"
echo "========================================"
echo ""

# Check required environment variables
if [ -z "$DATABASE_HOST" ]; then
    echo -e "${RED}❌ DATABASE_HOST environment variable is not set${NC}"
    exit 1
fi

if [ -z "$DATABASE_NAME" ]; then
    echo -e "${RED}❌ DATABASE_NAME environment variable is not set${NC}"
    exit 1
fi

if [ -z "$DATABASE_USER" ]; then
    echo -e "${RED}❌ DATABASE_USER environment variable is not set${NC}"
    exit 1
fi

if [ -z "$DATABASE_PASSWORD" ]; then
    echo -e "${RED}❌ DATABASE_PASSWORD environment variable is not set${NC}"
    exit 1
fi

# Build connection string
export PGPASSWORD="$DATABASE_PASSWORD"
PSQL_CMD="psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME -v ON_ERROR_STOP=1"

echo -e "${GREEN}✅ Environment variables configured${NC}"
echo ""

# Test database connection
echo "Testing database connection..."
if $PSQL_CMD -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database connection successful${NC}"
else
    echo -e "${RED}❌ Failed to connect to database${NC}"
    exit 1
fi
echo ""

# Function to apply a schema file
apply_schema() {
    local schema_file=$1
    local filename=$(basename "$schema_file")
    
    echo "----------------------------------------"
    echo "Applying schema: $filename"
    echo "----------------------------------------"
    
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${YELLOW}[DRY RUN] Would apply: $schema_file${NC}"
        cat "$schema_file"
        echo ""
        return 0
    fi
    
    if $PSQL_CMD -f "$schema_file"; then
        echo -e "${GREEN}✅ Successfully applied: $filename${NC}"
    else
        echo -e "${RED}❌ Failed to apply: $filename${NC}"
        return 1
    fi
    
    echo ""
}

# Apply schema files in order
echo "Applying database schemas..."
echo ""

SCHEMA_FILES=(
    # Note: 01_normalized_transactions.sql is deprecated (raw events now in Blob Storage)
    # Using updated schema that matches WO-11 implementation
    "$SCHEMA_DIR/02_dynamic_metrics_updated.sql"
    "$SCHEMA_DIR/03_payment_metrics_5m.sql"
    "$SCHEMA_DIR/04_failed_items.sql"
    "$SCHEMA_DIR/05_aggregate_histograms.sql"
)

FAILED=false

for schema_file in "${SCHEMA_FILES[@]}"; do
    if [ -f "$schema_file" ]; then
        if ! apply_schema "$schema_file"; then
            FAILED=true
            break
        fi
    else
        echo -e "${RED}❌ Schema file not found: $schema_file${NC}"
        FAILED=true
        break
    fi
done

# Summary
echo "========================================"
if [ "$FAILED" = "true" ]; then
    echo -e "${RED}❌ Schema deployment failed!${NC}"
    echo "========================================"
    exit 1
else
    echo -e "${GREEN}✅ Schema deployment completed successfully!${NC}"
    echo "========================================"
    
    # Display table summary
    echo ""
    echo "Database Tables:"
    $PSQL_CMD -c "\dt"
    
    echo ""
    echo "Table Sizes:"
    $PSQL_CMD -c "SELECT 
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
fi

# Clean up
unset PGPASSWORD

