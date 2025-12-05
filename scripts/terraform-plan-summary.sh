#!/bin/bash
#
# Terraform Plan Summary Generator
# Creates a human-readable summary of Terraform plan output
#

set -e

PLAN_FILE=${1:-"tfplan"}

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ ! -f "$PLAN_FILE" ]; then
    echo -e "${RED}❌ Plan file not found: $PLAN_FILE${NC}"
    exit 1
fi

echo "========================================"
echo "Terraform Plan Summary"
echo "========================================"
echo ""

# Get plan summary
PLAN_OUTPUT=$(terraform show -no-color "$PLAN_FILE")

# Count changes
TO_ADD=$(echo "$PLAN_OUTPUT" | grep -c "will be created" || true)
TO_CHANGE=$(echo "$PLAN_OUTPUT" | grep -c "will be updated" || true)
TO_DESTROY=$(echo "$PLAN_OUTPUT" | grep -c "will be destroyed" || true)

echo "📊 Changes Summary:"
echo "==================="
echo -e "${GREEN}➕ Resources to add:     $TO_ADD${NC}"
echo -e "${YELLOW}🔄 Resources to change:  $TO_CHANGE${NC}"
echo -e "${RED}➖ Resources to destroy: $TO_DESTROY${NC}"
echo ""

TOTAL_CHANGES=$((TO_ADD + TO_CHANGE + TO_DESTROY))

if [ $TOTAL_CHANGES -eq 0 ]; then
    echo -e "${GREEN}✅ No changes detected. Infrastructure is up to date.${NC}"
else
    echo -e "${BLUE}📝 Total changes: $TOTAL_CHANGES${NC}"
    echo ""
    echo "Detailed Changes:"
    echo "=================="
    terraform show "$PLAN_FILE" | grep -E "(will be created|will be updated|will be destroyed)" || true
fi

echo ""
echo "========================================"

