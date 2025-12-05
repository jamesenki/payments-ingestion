# Deployment Guide

## Quick Start

This guide walks you through deploying the Payments Ingestion infrastructure to Azure using the automated CI/CD pipeline.

## Prerequisites

Before deploying, ensure you have:

### Required Tools
- ✅ Git
- ✅ GitHub account with access to the repository
- ✅ Azure subscription(s)
- ✅ Azure CLI installed and configured
- ✅ Terraform 1.6.0+ (for local testing)

### Required Permissions
- ✅ Contributor role on target Azure subscription(s)
- ✅ Permission to create Service Principals in Azure AD
- ✅ Admin access to GitHub repository (to configure secrets)

## Initial Setup

### Step 1: Create Azure Resources for Terraform State (Optional but Recommended)

For production use, store Terraform state in Azure Storage:

```bash
# Set variables
RESOURCE_GROUP="terraform-state-rg"
STORAGE_ACCOUNT="tfstate$(openssl rand -hex 4)"
CONTAINER="tfstate"
LOCATION="eastus"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --encryption-services blob

# Create container
az storage container create \
  --name $CONTAINER \
  --account-name $STORAGE_ACCOUNT

echo "Storage account: $STORAGE_ACCOUNT"
```

### Step 2: Create Azure Service Principals

Create separate service principals for each environment:

```bash
# Get your subscription ID
az account show --query id -o tsv

# Development Environment
az ad sp create-for-rbac \
  --name "payments-ingestion-dev-sp" \
  --role contributor \
  --scopes /subscriptions/YOUR_DEV_SUBSCRIPTION_ID \
  --sdk-auth > dev-sp.json

# Staging Environment
az ad sp create-for-rbac \
  --name "payments-ingestion-staging-sp" \
  --role contributor \
  --scopes /subscriptions/YOUR_STAGING_SUBSCRIPTION_ID \
  --sdk-auth > staging-sp.json

# Production Environment
az ad sp create-for-rbac \
  --name "payments-ingestion-prod-sp" \
  --role contributor \
  --scopes /subscriptions/YOUR_PROD_SUBSCRIPTION_ID \
  --sdk-auth > prod-sp.json
```

**⚠️ Important:** Save these JSON files securely - you'll need them for GitHub secrets.

### Step 3: Configure GitHub Secrets

#### Navigate to GitHub Settings
1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

#### Add Global Secrets

| Secret Name | Value | How to Get |
|------------|-------|------------|
| `AZURE_TENANT_ID` | Your Azure AD Tenant ID | `az account show --query tenantId -o tsv` |
| `SNYK_TOKEN` | Snyk API token (optional) | Get from snyk.io account settings |

#### Add Development Secrets

From `dev-sp.json`:

| Secret Name | Value Source |
|------------|--------------|
| `DEV_AZURE_CLIENT_ID` | `clientId` from JSON |
| `DEV_AZURE_CLIENT_SECRET` | `clientSecret` from JSON |
| `DEV_AZURE_SUBSCRIPTION_ID` | `subscriptionId` from JSON |
| `DEV_POSTGRESQL_PASSWORD` | Generate strong password |

#### Add Staging Secrets

From `staging-sp.json`:

| Secret Name | Value Source |
|------------|--------------|
| `STAGING_AZURE_CLIENT_ID` | `clientId` from JSON |
| `STAGING_AZURE_CLIENT_SECRET` | `clientSecret` from JSON |
| `STAGING_AZURE_SUBSCRIPTION_ID` | `subscriptionId` from JSON |
| `STAGING_POSTGRESQL_PASSWORD` | Generate strong password |

#### Add Production Secrets

From `prod-sp.json`:

| Secret Name | Value Source |
|------------|--------------|
| `PROD_AZURE_CLIENT_ID` | `clientId` from JSON |
| `PROD_AZURE_CLIENT_SECRET` | `clientSecret` from JSON |
| `PROD_AZURE_SUBSCRIPTION_ID` | `subscriptionId` from JSON |
| `PROD_POSTGRESQL_PASSWORD` | Generate strong password |

**🔐 Security Tip:** Use a password generator for PostgreSQL passwords:
```bash
openssl rand -base64 32
```

### Step 4: Configure Terraform Backend (Optional)

If using remote state, update each environment's `main.tf`:

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstateXXXXXXXX"  # Use your storage account name
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"  # Change per environment
  }
}
```

### Step 5: Configure GitHub Environment Protection (Recommended)

For staging and production:

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Create environments: `staging`, `production`
4. For each environment:
   - ✅ Add required reviewers (1-6 people)
   - ✅ Add deployment branch protection (only `main`)
   - ✅ Set wait timer (optional, e.g., 5 minutes for staging)

## Deployment Workflows

### 🎯 First-Time Deployment

#### Step 1: Deploy to Development

**Option A: Via GitHub Actions (Recommended)**

1. Make a small change to trigger the pipeline (e.g., update README)
2. Commit and push to a feature branch
3. Create Pull Request to `main`
4. Review Terraform plan in PR comments
5. Merge PR → **Automatically deploys to dev**

**Option B: Manual Trigger**

1. Go to **Actions** → **Deploy to Dev Environment**
2. Click **Run workflow**
3. Branch: `main`
4. Action: `apply`
5. Click **Run workflow** button

#### Step 2: Verify Development Deployment

```bash
# Login to Azure
az login

# Check resources
az resource list --resource-group payments-ingestion-dev-rg -o table

# Check Event Hub
az eventhubs namespace show \
  --resource-group payments-ingestion-dev-rg \
  --name payments-ingestion-dev-evhns-eus

# Check Function App
az functionapp list \
  --resource-group payments-ingestion-dev-rg -o table

# Check PostgreSQL
az postgres flexible-server list \
  --resource-group payments-ingestion-dev-rg -o table
```

#### Step 3: Deploy to Staging

1. Go to **Actions** → **Deploy to Staging Environment**
2. Click **Run workflow**
3. Branch: `main`
4. Action: `apply`
5. Click **Run workflow**
6. **Approve deployment** if environment protection is enabled

#### Step 4: Deploy to Production

1. Go to **Actions** → **Deploy to Production Environment**
2. Click **Run workflow**
3. Branch: `main`
4. Action: `apply`
5. Confirm: Type `DEPLOY`
6. Click **Run workflow**
7. **Approve deployment** (if environment protection is enabled)

## Common Deployment Scenarios

### Deploying a Code Change

```bash
# 1. Create feature branch
git checkout -b feature/add-new-resource

# 2. Make changes to IaC
vim iac/environments/dev/main.tf

# 3. Validate locally
./scripts/validate-terraform.sh

# 4. Commit and push
git add .
git commit -m "Add new resource to dev environment"
git push origin feature/add-new-resource

# 5. Create Pull Request
# - Review Terraform plan in PR comments
# - Request code review
# - Merge when approved

# 6. Deployment happens automatically to dev
# 7. Manually deploy to staging/prod as needed
```

### Deploying to Multiple Environments

For changes that affect all environments:

```bash
# 1. Test in dev first (auto-deploy on merge)
git checkout main
git pull

# 2. Verify dev is working
az resource list --resource-group payments-ingestion-dev-rg

# 3. Deploy to staging
# Use GitHub Actions UI: Deploy to Staging Environment

# 4. Run smoke tests in staging
# Verify all resources are healthy

# 5. Deploy to production (requires confirmation)
# Use GitHub Actions UI: Deploy to Production Environment
```

### Emergency Hotfix Deployment

For critical production fixes:

```bash
# 1. Create hotfix branch from main
git checkout main
git pull
git checkout -b hotfix/critical-fix

# 2. Make minimal required changes
vim iac/environments/production/main.tf

# 3. Validate
./scripts/validate-terraform.sh

# 4. Create PR with "HOTFIX" label
git add .
git commit -m "HOTFIX: Fix critical production issue"
git push origin hotfix/critical-fix

# 5. Get emergency approval and merge

# 6. Deploy directly to production
# Use GitHub Actions: Deploy to Production
# Type "DEPLOY" to confirm
```

## Validation and Testing

### Pre-Deployment Validation

Before deploying, always run:

```bash
# Validate Terraform syntax
./scripts/validate-terraform.sh

# Check for infrastructure drift
./scripts/check-drift.sh dev
./scripts/check-drift.sh staging
./scripts/check-drift.sh production
```

### Post-Deployment Verification

After deployment, verify:

```bash
# Check all resources are created
az resource list --resource-group <resource-group-name> -o table

# Check resource health
az resource list --resource-group <resource-group-name> --query "[?provisioningState!='Succeeded']" -o table

# Test Event Hub connection
az eventhubs eventhub show \
  --resource-group <resource-group> \
  --namespace-name <namespace> \
  --name <eventhub-name>

# Test PostgreSQL connection
psql "host=<server-fqdn> port=5432 dbname=payments_db user=psqladmin sslmode=require"

# Check Function App status
az functionapp show \
  --resource-group <resource-group> \
  --name <function-app-name> \
  --query state -o tsv
```

## Troubleshooting

### Deployment Fails

**Check workflow logs:**
1. Go to **Actions** tab
2. Click on failed workflow run
3. Expand failed step
4. Review error messages

**Common issues:**

| Error | Solution |
|-------|----------|
| "Resource name already exists" | Choose a different name or delete existing resource |
| "Insufficient permissions" | Verify service principal has contributor role |
| "Quota exceeded" | Request quota increase from Azure support |
| "State lock timeout" | Wait for other operations to complete or force-unlock |

### Plan Shows Unexpected Changes

```bash
# Check for drift
./scripts/check-drift.sh <environment>

# Review state
cd iac/environments/<environment>
terraform state list
terraform state show <resource-address>
```

### Need to Rollback

```bash
# Option 1: Revert commit and redeploy
git revert <commit-hash>
git push origin main

# Option 2: Apply previous plan (if available)
# Download artifact from previous successful workflow
# Apply manually

# Option 3: Destroy and recreate (dev/staging only)
# Use "Destroy Infrastructure" workflow
```

### Access Denied Errors

```bash
# Verify authentication
az login
az account show

# Check service principal permissions
az role assignment list --assignee <client-id> -o table

# Re-authenticate if needed
az login --service-principal \
  -u <client-id> \
  -p <client-secret> \
  --tenant <tenant-id>
```

## Maintenance

### Regular Tasks

**Weekly:**
- ✅ Check for infrastructure drift
- ✅ Review failed workflow runs
- ✅ Monitor Azure costs

**Monthly:**
- ✅ Review and rotate service principal credentials
- ✅ Update Terraform provider versions
- ✅ Review security scan results
- ✅ Test disaster recovery procedures

**Quarterly:**
- ✅ Review and update all documentation
- ✅ Audit GitHub secrets
- ✅ Validate backup and restore procedures

### Updating Terraform Version

```bash
# 1. Update .terraform-version file
echo "1.6.0" > .terraform-version

# 2. Update workflows
# Edit: .github/workflows/reusable-terraform.yml
# Change: terraform_version: 1.6.0

# 3. Test locally with new version
terraform version
./scripts/validate-terraform.sh

# 4. Deploy to dev first for testing
```

### Rotating Credentials

```bash
# 1. Create new service principal
az ad sp create-for-rbac \
  --name "payments-ingestion-dev-sp-v2" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
  --sdk-auth

# 2. Update GitHub secrets with new credentials

# 3. Test deployment with new credentials

# 4. Delete old service principal
az ad sp delete --id <old-sp-id>
```

## Best Practices

### 1. Always Use Feature Branches
- Never commit directly to `main`
- Use descriptive branch names: `feature/`, `bugfix/`, `hotfix/`
- Keep PRs small and focused

### 2. Review Plans Before Apply
- Always review the Terraform plan
- Look for unexpected resource changes
- Verify resource counts match expectations

### 3. Progressive Rollout
- Deploy to dev first
- Test thoroughly in staging
- Production deployments during business hours
- Have rollback plan ready

### 4. Documentation
- Document all manual changes
- Keep deployment notes
- Update runbooks as needed

### 5. Security
- Use strong, unique passwords
- Rotate credentials regularly
- Enable MFA on all accounts
- Review access logs monthly

### 6. Cost Management
- Monitor Azure costs daily
- Set up budget alerts
- Right-size resources in non-prod
- Delete unused dev environments

## Emergency Contacts

### Escalation Path

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| Production Outage | On-call engineer | 15 minutes |
| Security Incident | Security team | 30 minutes |
| Azure Platform Issues | Azure Support | 1 hour |
| Pipeline Issues | DevOps team | Next business day |

## Additional Resources

- [Terraform Azure Provider Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure CLI Reference](https://docs.microsoft.com/en-us/cli/azure/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [CI/CD Pipeline Documentation](./CI-CD-PIPELINE.md)

## Appendix

### Environment Comparison

| Feature | Dev | Staging | Production |
|---------|-----|---------|------------|
| Auto-deploy | ✅ Yes | ❌ No | ❌ No |
| Approval required | ❌ No | ✅ Yes | ✅ Yes |
| Event Hub SKU | Standard | Standard | Standard |
| Event Hub Capacity | 1 | 2 | 4 |
| PostgreSQL SKU | B_Standard_B1ms | GP_Standard_D2s_v3 | GP_Standard_D4s_v3 |
| Storage Replication | LRS | GRS | GZRS |
| Backup Retention | 7 days | 14 days | 35 days |
| High Availability | Disabled | ZoneRedundant | ZoneRedundant |

### Terraform State Management

**State Location:**
- Local: `iac/environments/<env>/terraform.tfstate` (not recommended for prod)
- Remote: Azure Storage Account (recommended)

**State Operations:**

```bash
# List resources in state
terraform state list

# Show resource details
terraform state show <resource-address>

# Move resource in state
terraform state mv <source> <destination>

# Remove resource from state
terraform state rm <resource-address>

# Pull remote state
terraform state pull > local-state.json
```

### Resource Naming Convention

Pattern: `{project}-{environment}-{resource}-{region}`

Examples:
- `payments-ingestion-dev-evhns-eus`
- `payments-ingestion-prod-func-eus`
- `payments-ingestion-staging-psql-eus`

### Cost Estimates

**Development (monthly):**
- Event Hub: $10-20
- Function App: $0-10 (consumption)
- PostgreSQL: $20-40
- Storage: $5-10
- **Total: ~$35-80/month**

**Production (monthly):**
- Event Hub: $80-150
- Function App: $150-300 (premium)
- PostgreSQL: $200-400
- Storage: $20-50
- **Total: ~$450-900/month**

---

**Last Updated:** December 2025  
**Version:** 1.0  
**Maintained by:** Infrastructure Team

