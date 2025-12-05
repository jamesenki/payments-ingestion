# CI/CD Pipeline Documentation

## Overview

This document describes the automated CI/CD pipeline for the Payments Ingestion infrastructure, built with GitHub Actions and Terraform.

## Architecture

```
┌─────────────────┐
│  Pull Request   │
│   (any branch)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  PR Validation Pipeline │
│  • Format Check         │
│  • Validate             │
│  • Plan (affected envs) │
│  • Security Scan (Snyk) │
└────────┬────────────────┘
         │
         ▼
┌────────────────────┐
│  Merge to main     │
└────────┬───────────┘
         │
         ▼
┌──────────────────────┐
│  Auto Deploy to Dev  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────┐
│  Manual Deploy: Staging  │
│  (workflow_dispatch)     │
└──────────┬───────────────┘
           │
           ▼
┌───────────────────────────┐
│  Manual Deploy: Production│
│  (requires confirmation)  │
└───────────────────────────┘
```

## Workflows

### 1. **terraform-plan.yml** - Pull Request Validation

**Trigger:** Pull requests to `main` branch with changes to IaC files

**Purpose:** Validate Terraform changes before merge

**Steps:**
1. **Detect Changes** - Identifies which environments are affected
2. **Security Scan** - Runs Snyk IaC scan for security vulnerabilities
3. **Terraform Plan** - Generates execution plan for each affected environment
4. **Comment Results** - Posts plan summary as PR comment

**Secrets Required:**
- Per-environment Azure credentials
- `SNYK_TOKEN` (optional, for security scanning)

### 2. **terraform-deploy-dev.yml** - Development Deployment

**Trigger:** 
- Push to `main` branch (auto-deploy)
- Manual workflow dispatch

**Purpose:** Automatically deploy changes to the development environment

**Steps:**
1. Terraform plan
2. Terraform apply (if action is 'apply')
3. Notify deployment status

**Environment Protection:** None (auto-deploy)

### 3. **terraform-deploy-staging.yml** - Staging Deployment

**Trigger:** Manual workflow dispatch only

**Purpose:** Deploy to staging environment for pre-production testing

**Steps:**
1. Terraform plan/apply
2. Run smoke tests
3. Notify deployment status

**Environment Protection:** Manual approval recommended (configure in GitHub settings)

### 4. **terraform-deploy-production.yml** - Production Deployment

**Trigger:** Manual workflow dispatch only

**Purpose:** Deploy to production environment

**Steps:**
1. **Validate Confirmation** - Requires typing "DEPLOY" to proceed
2. Terraform plan/apply
3. Run production health checks
4. Create deployment tag
5. Notify deployment status

**Environment Protection:** 
- Manual approval required
- Confirmation string required
- Defaults to 'plan' action for safety

**Safety Features:**
- Requires explicit confirmation: `DEPLOY`
- Creates git tags for each production deployment
- Runs health checks post-deployment

### 5. **terraform-destroy.yml** - Infrastructure Teardown

**Trigger:** Manual workflow dispatch only

**Purpose:** Safely destroy infrastructure for dev/staging environments

**Available Environments:** `dev`, `staging` only (production excluded)

**Steps:**
1. Validate confirmation (must type environment name)
2. Run terraform destroy
3. Notify completion

**Safety Features:**
- Requires exact environment name as confirmation
- Production environment cannot be destroyed via workflow
- Manual workflow dispatch only

### 6. **reusable-terraform.yml** - Shared Workflow Template

**Purpose:** Reusable workflow called by other workflows to reduce duplication

**Inputs:**
- `environment` - Target environment (dev/staging/production)
- `terraform_action` - Action to perform (plan/apply/destroy)
- `working_directory` - Path to Terraform configuration

**Features:**
- Azure authentication
- Terraform fmt/init/validate/plan/apply/destroy
- Artifact uploads (plans, state info)
- Consistent error handling

## GitHub Secrets Configuration

### Global Secrets

| Secret Name | Description | Required |
|------------|-------------|----------|
| `AZURE_TENANT_ID` | Azure AD Tenant ID | ✅ Yes |
| `SNYK_TOKEN` | Snyk API token for security scanning | ⚠️ Optional |

### Development Environment Secrets

| Secret Name | Description |
|------------|-------------|
| `DEV_AZURE_CLIENT_ID` | Service Principal Client ID |
| `DEV_AZURE_CLIENT_SECRET` | Service Principal Client Secret |
| `DEV_AZURE_SUBSCRIPTION_ID` | Azure Subscription ID |
| `DEV_POSTGRESQL_PASSWORD` | PostgreSQL admin password |

### Staging Environment Secrets

| Secret Name | Description |
|------------|-------------|
| `STAGING_AZURE_CLIENT_ID` | Service Principal Client ID |
| `STAGING_AZURE_CLIENT_SECRET` | Service Principal Client Secret |
| `STAGING_AZURE_SUBSCRIPTION_ID` | Azure Subscription ID |
| `STAGING_POSTGRESQL_PASSWORD` | PostgreSQL admin password |

### Production Environment Secrets

| Secret Name | Description |
|------------|-------------|
| `PROD_AZURE_CLIENT_ID` | Service Principal Client ID |
| `PROD_AZURE_CLIENT_SECRET` | Service Principal Client Secret |
| `PROD_AZURE_SUBSCRIPTION_ID` | Azure Subscription ID |
| `PROD_POSTGRESQL_PASSWORD` | PostgreSQL admin password |

## Setting Up the Pipeline

### 1. Create Azure Service Principals

```bash
# Development
az ad sp create-for-rbac --name "payments-ingestion-dev-sp" \
  --role contributor \
  --scopes /subscriptions/YOUR_DEV_SUBSCRIPTION_ID \
  --sdk-auth

# Staging
az ad sp create-for-rbac --name "payments-ingestion-staging-sp" \
  --role contributor \
  --scopes /subscriptions/YOUR_STAGING_SUBSCRIPTION_ID \
  --sdk-auth

# Production
az ad sp create-for-rbac --name "payments-ingestion-prod-sp" \
  --role contributor \
  --scopes /subscriptions/YOUR_PROD_SUBSCRIPTION_ID \
  --sdk-auth
```

Save the output JSON - you'll need these values for GitHub secrets.

### 2. Configure GitHub Secrets

Run the helper script for guidance:

```bash
./scripts/setup-github-secrets.sh
```

Or manually add secrets in GitHub:
1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret from the tables above

### 3. Configure Environment Protection Rules (Optional)

For staging and production environments:

1. Go to repository Settings → Environments
2. Create environments: `dev`, `staging`, `production`
3. For `staging` and `production`:
   - Add required reviewers
   - Set deployment branch restrictions
   - Configure wait timers if desired

### 4. Enable GitHub Actions

1. Go to repository Settings → Actions → General
2. Ensure "Allow all actions and reusable workflows" is selected
3. Save settings

## Usage

### Deploying Changes

#### Development (Automatic)
1. Create a feature branch
2. Make infrastructure changes
3. Create pull request to `main`
4. Review the Terraform plan in PR comments
5. Merge PR → **Automatically deploys to dev**

#### Staging (Manual)
1. Ensure changes are merged to `main`
2. Go to Actions → "Deploy to Staging Environment"
3. Click "Run workflow"
4. Select action: `apply`
5. Approve deployment (if protection rules are set)

#### Production (Manual with Confirmation)
1. Ensure changes are tested in staging
2. Go to Actions → "Deploy to Production Environment"
3. Click "Run workflow"
4. Select action: `apply`
5. **Type `DEPLOY` in the confirmation field**
6. Approve deployment (if protection rules are set)

### Running Plans Only

For any environment:
1. Go to Actions → Select deployment workflow
2. Click "Run workflow"
3. Select action: `plan`
4. Review the plan in workflow logs

### Destroying Infrastructure

⚠️ **Use with caution!** Only available for dev and staging.

1. Go to Actions → "Destroy Infrastructure (Manual)"
2. Click "Run workflow"
3. Select environment: `dev` or `staging`
4. **Type the environment name** in the confirmation field
5. Click "Run workflow"

## Helper Scripts

### validate-terraform.sh

Validates all Terraform configurations locally.

```bash
./scripts/validate-terraform.sh
```

**What it does:**
- Checks Terraform formatting
- Runs `terraform init` for all environments
- Runs `terraform validate` for all environments

### check-drift.sh

Detects infrastructure drift for an environment.

```bash
./scripts/check-drift.sh <environment>
```

**Example:**
```bash
./scripts/check-drift.sh dev
```

**What it does:**
- Compares Terraform state with actual Azure infrastructure
- Reports any drift detected
- Saves detailed drift report

### terraform-plan-summary.sh

Generates human-readable plan summaries.

```bash
./scripts/terraform-plan-summary.sh <plan-file>
```

**What it does:**
- Counts resources to add/change/destroy
- Provides formatted summary output

### setup-github-secrets.sh

Provides guidance for setting up GitHub secrets.

```bash
./scripts/setup-github-secrets.sh
```

## Troubleshooting

### Pipeline Fails on PR

**Symptom:** Terraform plan fails during PR validation

**Solutions:**
1. Check that secrets are configured correctly
2. Verify service principal has necessary permissions
3. Run `./scripts/validate-terraform.sh` locally
4. Check Azure subscription limits/quotas

### Deployment Hangs

**Symptom:** Workflow stays in "Waiting" status

**Solutions:**
1. Check environment protection rules in GitHub settings
2. Approve the deployment if protection rules require it
3. Check workflow dispatch inputs are correct

### Authentication Errors

**Symptom:** "Error: Failed to get Azure credentials"

**Solutions:**
1. Verify `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, etc. are set correctly
2. Check service principal hasn't expired
3. Ensure service principal has contributor role on subscription

### State Lock Errors

**Symptom:** "Error acquiring the state lock"

**Solutions:**
1. Wait for other operations to complete
2. If stuck, manually release lock in Azure Portal (Storage Account → Containers → terraform state)
3. Verify only one workflow runs at a time per environment

## Best Practices

### 1. Always Review Plans
- Never apply without reviewing the plan first
- Use PR validation to catch issues early
- Run manual plans before production deploys

### 2. Progressive Deployment
- Always deploy to dev first
- Test in staging before production
- Use staging as production replica when possible

### 3. Security
- Rotate service principal credentials regularly
- Use different credentials per environment
- Store sensitive values in Azure Key Vault
- Enable audit logging on GitHub Actions

### 4. Disaster Recovery
- Test rollback procedures regularly
- Keep deployment tags for production releases
- Maintain separate Azure subscriptions per environment
- Document recovery procedures

### 5. Monitoring
- Check workflow run history regularly
- Set up notifications for failed deployments
- Monitor infrastructure drift weekly
- Review security scan results

## Rollback Procedures

### Rolling Back a Deployment

If a deployment causes issues:

1. **Quick Fix:** Revert the commit and deploy
   ```bash
   git revert <commit-hash>
   git push origin main
   ```

2. **Manual Rollback:** Use previous plan
   - Download artifact from previous successful deployment
   - Apply the previous plan manually

3. **Emergency:** Destroy and recreate
   - Use destroy workflow (dev/staging only)
   - Redeploy from last known good state

### Production Rollback

For production issues:
1. Assess impact immediately
2. If critical: Contact Azure support
3. Use git revert + redeploy for code issues
4. Consider manual fixes in Azure Portal for emergencies (document changes!)

## Additional Resources

- [Terraform Azure Provider Documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure Service Principals](https://docs.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals)

## Support

For issues with the CI/CD pipeline:
1. Check this documentation
2. Review workflow logs in GitHub Actions
3. Run validation scripts locally
4. Check Azure resource health in Portal

