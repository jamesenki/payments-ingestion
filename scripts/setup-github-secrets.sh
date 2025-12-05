#!/bin/bash
#
# Setup GitHub Secrets for CI/CD
# Helper script to guide through setting up required GitHub secrets
#

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================"
echo "GitHub Secrets Setup Guide"
echo "========================================"
echo ""

echo -e "${BLUE}This script will guide you through setting up the required GitHub secrets for the CI/CD pipeline.${NC}"
echo ""

echo "Required GitHub Secrets by Environment:"
echo ""

echo "========================================" 
echo "GLOBAL SECRETS (all environments)"
echo "========================================"
echo "• AZURE_TENANT_ID          - Your Azure AD tenant ID"
echo "• SNYK_TOKEN               - Snyk API token for security scanning (optional)"
echo ""

echo "========================================"
echo "DEV ENVIRONMENT SECRETS"
echo "========================================"
echo "• DEV_AZURE_CLIENT_ID      - Service Principal Client ID for Dev"
echo "• DEV_AZURE_CLIENT_SECRET  - Service Principal Client Secret for Dev"
echo "• DEV_AZURE_SUBSCRIPTION_ID - Azure Subscription ID for Dev"
echo "• DEV_POSTGRESQL_PASSWORD  - PostgreSQL admin password for Dev"
echo ""

echo "========================================"
echo "STAGING ENVIRONMENT SECRETS"
echo "========================================"
echo "• STAGING_AZURE_CLIENT_ID      - Service Principal Client ID for Staging"
echo "• STAGING_AZURE_CLIENT_SECRET  - Service Principal Client Secret for Staging"
echo "• STAGING_AZURE_SUBSCRIPTION_ID - Azure Subscription ID for Staging"
echo "• STAGING_POSTGRESQL_PASSWORD  - PostgreSQL admin password for Staging"
echo ""

echo "========================================"
echo "PRODUCTION ENVIRONMENT SECRETS"
echo "========================================"
echo "• PROD_AZURE_CLIENT_ID      - Service Principal Client ID for Production"
echo "• PROD_AZURE_CLIENT_SECRET  - Service Principal Client Secret for Production"
echo "• PROD_AZURE_SUBSCRIPTION_ID - Azure Subscription ID for Production"
echo "• PROD_POSTGRESQL_PASSWORD  - PostgreSQL admin password for Production"
echo ""

echo "========================================"
echo "How to Set GitHub Secrets"
echo "========================================"
echo "1. Go to your GitHub repository"
echo "2. Navigate to Settings > Secrets and variables > Actions"
echo "3. Click 'New repository secret'"
echo "4. Add each secret with the exact name shown above"
echo ""

echo "========================================"
echo "Creating Azure Service Principals"
echo "========================================"
echo ""
echo "Run the following Azure CLI commands to create service principals:"
echo ""

echo -e "${YELLOW}# For Dev Environment:${NC}"
echo "az ad sp create-for-rbac --name \"payments-ingestion-dev-sp\" \\"
echo "  --role contributor \\"
echo "  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \\"
echo "  --sdk-auth"
echo ""

echo -e "${YELLOW}# For Staging Environment:${NC}"
echo "az ad sp create-for-rbac --name \"payments-ingestion-staging-sp\" \\"
echo "  --role contributor \\"
echo "  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \\"
echo "  --sdk-auth"
echo ""

echo -e "${YELLOW}# For Production Environment:${NC}"
echo "az ad sp create-for-rbac --name \"payments-ingestion-prod-sp\" \\"
echo "  --role contributor \\"
echo "  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \\"
echo "  --sdk-auth"
echo ""

echo "========================================"
echo "Getting Your Azure Tenant ID"
echo "========================================"
echo "az account show --query tenantId -o tsv"
echo ""

echo "========================================"
echo "Security Best Practices"
echo "========================================"
echo "✓ Use different service principals for each environment"
echo "✓ Apply least privilege access (only necessary permissions)"
echo "✓ Rotate secrets regularly"
echo "✓ Use strong, randomly generated PostgreSQL passwords"
echo "✓ Store passwords in Azure Key Vault for production"
echo "✓ Enable audit logging for secret access"
echo ""

echo -e "${GREEN}✅ Setup guide complete!${NC}"
echo ""
echo "For more information, see: docs/CI-CD-PIPELINE.md"

