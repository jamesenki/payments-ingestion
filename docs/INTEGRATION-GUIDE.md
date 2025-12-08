# Integration Guide for Larger Projects

**Date:** December 7, 2025  
**Purpose:** Guide for integrating payments-ingestion deployment into larger project pipelines

---

## Overview

This guide explains how to integrate the payments-ingestion deployment scripts and workflows into a larger project's CI/CD pipeline.

---

## Architecture

### Deployment Components

```
┌─────────────────────────────────────────────────────────┐
│         Unified Deployment Orchestration                │
│              (scripts/deploy-all.sh)                    │
└─────────────────┬───────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
┌───────────┐ ┌──────────┐ ┌──────────────┐
│Infrastructure│ │ Database │ │ Function App │
│  (Terraform)  │ │  Schema  │ │     Code     │
└───────────┘ └──────────┘ └──────────────┘
```

### Component Dependencies

```
Infrastructure (Terraform)
    ↓
    ├─→ Database Schema (requires PostgreSQL)
    └─→ Function App Code (requires Function App)
```

---

## Integration Patterns

### Pattern 1: Standalone Deployment

**Use Case:** Deploy payments-ingestion independently

**Implementation:**
```bash
# Deploy everything
./scripts/deploy-all.sh dev

# Deploy specific components
DEPLOY_INFRASTRUCTURE=false ./scripts/deploy-all.sh dev  # Skip infra
DEPLOY_DATABASE=false ./scripts/deploy-all.sh dev        # Skip database
```

**GitHub Actions:**
```yaml
- name: Deploy Payments Ingestion
  run: |
    ./scripts/deploy-all.sh ${{ env.ENVIRONMENT }}
  env:
    AZURE_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
    # ... other env vars
```

---

### Pattern 2: Integrated into Larger Pipeline

**Use Case:** Payments-ingestion is part of a larger system

**Implementation:**
```yaml
jobs:
  deploy-payments-ingestion:
    name: Deploy Payments Ingestion
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy Infrastructure
        if: needs.deploy-other-services.success
        run: |
          cd iac/environments/${{ env.ENVIRONMENT }}
          terraform apply -auto-approve
      
      - name: Deploy Database Schema
        if: needs.deploy-infrastructure.success
        run: |
          ./scripts/database/deploy-schema.sh ${{ env.ENVIRONMENT }}
      
      - name: Deploy Function App Code
        if: needs.deploy-database.success
        uses: ./.github/workflows/function-app-deploy.yml
```

---

### Pattern 3: Modular Component Deployment

**Use Case:** Deploy components independently based on changes

**Implementation:**
```yaml
jobs:
  detect-changes:
    outputs:
      infra: ${{ steps.changes.outputs.infra }}
      database: ${{ steps.changes.outputs.database }}
      function: ${{ steps.changes.outputs.function }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v2
        id: changes
        with:
          filters: |
            infra:
              - 'iac/**'
            database:
              - 'database/**'
            function:
              - 'src/function_app/**'
  
  deploy-infra:
    if: needs.detect-changes.outputs.infra == 'true'
    # ... deploy infrastructure
  
  deploy-database:
    if: needs.detect-changes.outputs.database == 'true'
    # ... deploy database
  
  deploy-function:
    if: needs.detect-changes.outputs.function == 'true'
    # ... deploy function app
```

---

## Configuration Management

### Environment Variables

**Required Variables:**
```bash
# Azure Authentication
AZURE_SUBSCRIPTION_ID
AZURE_TENANT_ID
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET

# Database (per environment)
${ENV}_POSTGRESQL_PASSWORD
DATABASE_HOST
DATABASE_NAME
DATABASE_USER

# Function App (per environment)
${ENV}_FUNCTION_APP_NAME
${ENV}_RESOURCE_GROUP
```

**Recommended:** Use GitHub Secrets or Azure Key Vault

---

### Configuration Files

**Terraform Configuration:**
- `iac/environments/{env}/terraform.tfvars` - Environment-specific values
- `iac/environments/{env}/main.tf` - Environment configuration

**Database Configuration:**
- `database/schemas/*.sql` - Schema files
- `scripts/database/deploy-schema.sh` - Deployment script

**Function App Configuration:**
- `src/function_app/function.json` - Function bindings
- `requirements.txt` - Python dependencies

---

## API/Interface for Integration

### Script Interfaces

#### `scripts/deploy-all.sh`

**Usage:**
```bash
./scripts/deploy-all.sh [environment] [options]
```

**Options:**
- `--skip-infrastructure` - Skip Terraform deployment
- `--skip-database` - Skip database schema deployment
- `--skip-function-app` - Skip Function App code deployment
- `--skip-health-checks` - Skip post-deployment health checks
- `--dry-run` - Preview changes without applying

**Exit Codes:**
- `0` - Success
- `1` - Failure

**Output:**
- Logs to `deployment-{env}-{timestamp}.log`
- Returns JSON summary (future enhancement)

---

#### `scripts/database/deploy-schema.sh`

**Usage:**
```bash
./scripts/database/deploy-schema.sh [environment]
```

**Environment Variables:**
- `DATABASE_HOST` - PostgreSQL hostname
- `DATABASE_NAME` - Database name
- `DATABASE_USER` - Database username
- `DATABASE_PASSWORD` - Database password
- `DRY_RUN` - Set to "true" for dry run

**Exit Codes:**
- `0` - Success
- `1` - Failure

---

### GitHub Actions Workflows

#### Infrastructure Deployment

**Workflow:** `.github/workflows/reusable-terraform.yml`

**Inputs:**
- `environment` - Target environment
- `terraform_action` - plan, apply, or destroy
- `working_directory` - Terraform directory

**Secrets:**
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_TENANT_ID`
- `TF_VAR_postgresql_admin_password`

**Usage:**
```yaml
uses: ./.github/workflows/reusable-terraform.yml
with:
  environment: dev
  terraform_action: apply
  working_directory: ./iac/environments/dev
```

---

#### Database Schema Deployment

**Workflow:** `.github/workflows/database-deploy.yml`

**Inputs:**
- `environment` - Target environment
- `dry_run` - Preview changes
- `confirm` - Environment name confirmation

**Usage:**
```yaml
workflow_dispatch:
  inputs:
    environment: dev
    dry_run: false
    confirm: dev
```

---

#### Function App Code Deployment

**Workflow:** `.github/workflows/function-app-deploy.yml`

**Inputs:**
- `environment` - Target environment
- `version` - Version tag (optional)

**Usage:**
```yaml
workflow_dispatch:
  inputs:
    environment: dev
    version: v1.0.0
```

---

## Dependency Management

### Deployment Order

1. **Infrastructure** (Terraform)
   - Creates: Event Hub, Function App, PostgreSQL, Storage Account
   - Duration: ~5-10 minutes
   - Prerequisites: Azure subscription, credentials

2. **Database Schema**
   - Creates: Tables, indexes, constraints
   - Duration: ~1-2 minutes
   - Prerequisites: PostgreSQL exists (from step 1)

3. **Function App Code**
   - Deploys: Python code and dependencies
   - Duration: ~2-3 minutes
   - Prerequisites: Function App exists (from step 1)

4. **Health Checks**
   - Verifies: Function App status, database connectivity
   - Duration: ~30 seconds
   - Prerequisites: All components deployed

---

## Error Handling and Rollback

### Error Handling

**Current Implementation:**
- Scripts use `set -e` (exit on error)
- Each step validates prerequisites
- Clear error messages

**Recommended Enhancements:**
- Rollback mechanisms
- Deployment history tracking
- Automatic retry for transient failures

---

### Rollback Procedures

**Infrastructure Rollback:**
```bash
# Rollback to previous Terraform state
cd iac/environments/$ENVIRONMENT
terraform plan -destroy
terraform destroy -target=<resource>
```

**Database Schema Rollback:**
- Manual SQL scripts (not automated)
- Use database migrations for versioning

**Function App Rollback:**
```bash
# Deploy previous version
az functionapp deployment source config-zip \
  --resource-group $RG_NAME \
  --name $FUNC_APP_NAME \
  --src previous-deployment.zip
```

---

## Health Checks

### Post-Deployment Health Checks

**Function App:**
```bash
# Check Function App status
az functionapp show \
  --resource-group $RG_NAME \
  --name $FUNC_APP_NAME \
  --query "state"

# List deployed functions
az functionapp function list \
  --resource-group $RG_NAME \
  --name $FUNC_APP_NAME
```

**Database:**
```bash
# Test connectivity
psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME -c "SELECT 1;"

# Validate schema
./scripts/database/validate-schema.sh
```

**Event Hub:**
```bash
# Check Event Hub namespace
az eventhubs namespace show \
  --resource-group $RG_NAME \
  --name $EVH_NAMESPACE
```

---

## Integration Examples

### Example 1: Simple Integration

```yaml
name: Deploy All Services

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy Payments Ingestion
        run: |
          ./scripts/deploy-all.sh dev
        env:
          AZURE_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
          # ... other secrets
```

---

### Example 2: Conditional Deployment

```yaml
jobs:
  deploy-payments-ingestion:
    if: contains(github.event.head_commit.message, '[deploy-payments]')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/deploy-all.sh dev
```

---

### Example 3: Multi-Environment Deployment

```yaml
strategy:
  matrix:
    environment: [dev, staging, production]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ matrix.environment }}
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/deploy-all.sh ${{ matrix.environment }}
```

---

## Best Practices

### 1. Environment Isolation
- Use separate Azure subscriptions per environment
- Separate GitHub environments with protection rules
- Independent Terraform state files

### 2. Secret Management
- Use GitHub Secrets for CI/CD
- Use Azure Key Vault for runtime secrets
- Never commit secrets to repository

### 3. Deployment Order
- Always deploy infrastructure first
- Deploy database schema before Function App code
- Run health checks after deployment

### 4. Error Handling
- Validate prerequisites before deployment
- Use dry-run mode for testing
- Implement rollback procedures

### 5. Monitoring
- Log all deployment activities
- Track deployment history
- Monitor health checks

---

## Troubleshooting

### Common Issues

**Issue:** Terraform state locked
```bash
# Solution: Unlock state (use with caution)
terraform force-unlock <lock-id>
```

**Issue:** Database connection failed
```bash
# Solution: Verify credentials and network access
psql -h $DATABASE_HOST -U $DATABASE_USER -d $DATABASE_NAME -c "SELECT 1;"
```

**Issue:** Function App deployment failed
```bash
# Solution: Check Function App exists and is accessible
az functionapp show --resource-group $RG_NAME --name $FUNC_APP_NAME
```

---

## Future Enhancements

### Recommended Improvements

1. **Deployment History**
   - Track all deployments
   - Version tagging
   - Rollback automation

2. **Health Checks**
   - Automated health check endpoints
   - Integration with monitoring systems
   - Alerting on failures

3. **Rollback Automation**
   - Automatic rollback on critical failures
   - Previous version tracking
   - Blue-green deployments

4. **Configuration Management**
   - Centralized configuration
   - Environment-specific overrides
   - Configuration validation

5. **Integration APIs**
   - REST API for deployment
   - Webhook support
   - Status endpoints

---

## References

- [Deployment Guide](./DEPLOYMENT-GUIDE.md)
- [CI/CD Pipeline](./CI-CD-PIPELINE.md)
- [Database Deployment Scripts](../scripts/database/README.md)
- [Architecture Document](./ARCHITECTURE.md)

