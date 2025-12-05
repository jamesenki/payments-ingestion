#!/bin/bash
#
# Infrastructure Drift Detection Script
# Checks for drift between Terraform state and actual Azure infrastructure
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IaC_DIR="$PROJECT_ROOT/iac"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
ENVIRONMENT=${1:-"dev"}
VALID_ENVS=("dev" "staging" "production")

if [[ ! " ${VALID_ENVS[@]} " =~ " ${ENVIRONMENT} " ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo "Valid environments: ${VALID_ENVS[*]}"
    exit 1
fi

ENV_DIR="$IaC_DIR/environments/$ENVIRONMENT"

if [ ! -d "$ENV_DIR" ]; then
    echo -e "${RED}❌ Environment directory not found: $ENV_DIR${NC}"
    exit 1
fi

echo "========================================"
echo "Infrastructure Drift Detection"
echo "Environment: $ENVIRONMENT"
echo "========================================"
echo ""

# Check if logged into Azure
if ! az account show > /dev/null 2>&1; then
    echo -e "${RED}❌ Not logged into Azure${NC}"
    echo "Run: az login"
    exit 1
fi

echo -e "${GREEN}✅ Azure authentication verified${NC}"
echo ""

cd "$ENV_DIR"

# Initialize Terraform
echo "Initializing Terraform..."
if ! terraform init > /dev/null 2>&1; then
    echo -e "${RED}❌ Terraform init failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Terraform initialized${NC}"
echo ""

# Refresh state
echo "Refreshing Terraform state..."
if ! terraform refresh -lock=false > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Could not refresh state (may not exist yet)${NC}"
fi

# Check for drift
echo "Checking for infrastructure drift..."
echo ""

if terraform plan -detailed-exitcode -no-color > drift-report.txt 2>&1; then
    echo -e "${GREEN}✅ No drift detected!${NC}"
    echo "Infrastructure matches Terraform state."
    rm -f drift-report.txt
    exit 0
elif [ $? -eq 2 ]; then
    echo -e "${YELLOW}⚠️  DRIFT DETECTED!${NC}"
    echo ""
    echo "Changes detected between Terraform state and actual infrastructure:"
    echo "=================================================================="
    cat drift-report.txt
    echo "=================================================================="
    echo ""
    echo -e "${BLUE}ℹ️  Drift report saved to: $ENV_DIR/drift-report.txt${NC}"
    exit 2
else
    echo -e "${RED}❌ Error running terraform plan${NC}"
    cat drift-report.txt
    rm -f drift-report.txt
    exit 1
fi

