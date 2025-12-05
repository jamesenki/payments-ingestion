#!/bin/bash
#
# Terraform Validation Script
# Validates Terraform configuration files for all environments
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IaC_DIR="$PROJECT_ROOT/iac"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "Terraform Validation Script"
echo "======================================"
echo ""

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Terraform found: $(terraform version | head -n 1)${NC}"
echo ""

# Function to validate a terraform directory
validate_terraform_dir() {
    local dir=$1
    local env_name=$2
    
    echo "----------------------------------------"
    echo "Validating: $env_name"
    echo "Directory: $dir"
    echo "----------------------------------------"
    
    cd "$dir"
    
    # Format check
    echo "Running terraform fmt check..."
    if terraform fmt -check -recursive; then
        echo -e "${GREEN}✅ Format check passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Format check failed - files need formatting${NC}"
        echo "Run: terraform fmt -recursive"
        return 1
    fi
    
    # Initialize
    echo "Running terraform init..."
    if terraform init -backend=false > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Init passed${NC}"
    else
        echo -e "${RED}❌ Init failed${NC}"
        return 1
    fi
    
    # Validate
    echo "Running terraform validate..."
    if terraform validate; then
        echo -e "${GREEN}✅ Validate passed${NC}"
    else
        echo -e "${RED}❌ Validate failed${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ $env_name validation completed successfully${NC}"
    echo ""
    
    cd "$PROJECT_ROOT"
}

# Validate root IaC files
echo "========================================" 
echo "Validating Root IaC Configuration"
echo "========================================"
validate_terraform_dir "$IaC_DIR" "Root IaC"

# Validate each environment
ENVIRONMENTS=("dev" "staging" "production")

for env in "${ENVIRONMENTS[@]}"; do
    ENV_DIR="$IaC_DIR/environments/$env"
    if [ -d "$ENV_DIR" ]; then
        validate_terraform_dir "$ENV_DIR" "$env Environment"
    else
        echo -e "${YELLOW}⚠️  Environment directory not found: $ENV_DIR${NC}"
    fi
done

echo "========================================"
echo -e "${GREEN}✅ All validations completed successfully!${NC}"
echo "========================================"

