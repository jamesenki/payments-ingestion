# Testing Procedures for Phase 1

This document outlines the testing procedures for Phase 1 infrastructure and CI/CD pipeline validation.

## Overview

Phase 1 focuses on Infrastructure as Code and CI/CD pipeline validation. Testing ensures:
- Infrastructure deploys correctly across all environments
- CI/CD pipelines function as expected
- Security configurations are properly applied
- Documentation is accurate and complete

## Test Environments

| Environment | Purpose | Test Type |
|-------------|---------|-----------|
| Development | Unit & Integration | Manual + Automated |
| Staging | System & Performance | Manual + Automated |
| Production | Smoke Tests | Automated Only |

## Pre-Deployment Testing

### 1. Terraform Validation

**Purpose**: Verify Terraform syntax and configuration

**Procedure**:
```bash
# Run validation script
./scripts/validate-terraform.sh

# Expected Output:
# ✅ Terraform found
# ✅ Format check passed
# ✅ Init passed
# ✅ Validate passed (for all environments)
```

**Pass Criteria**:
- All format checks pass
- All terraform validate commands succeed
- No syntax errors

### 2. Security Scanning (Snyk IaC)

**Purpose**: Identify security vulnerabilities in infrastructure code

**Procedure**:
```bash
# Scan IaC directory
snyk iac test iac/

# Or use the automated PR workflow
```

**Pass Criteria**:
- No critical or high severity issues
- Medium issues reviewed and accepted
- Scan completes without errors

### 3. Pull Request Validation

**Purpose**: Automated validation on code changes

**Procedure**:
1. Create feature branch
2. Make changes to IaC
3. Create Pull Request to main
4. Wait for GitHub Actions to complete

**Automated Checks**:
- ✅ Terraform format check
- ✅ Terraform validate
- ✅ Terraform plan for affected environments
- ✅ Snyk security scan
- ✅ Plan results posted as PR comment

**Pass Criteria**:
- All checks pass (green)
- Plan output shows expected changes only
- No unexpected resource deletions
- Security scan passes

## Infrastructure Deployment Testing

### 1. Development Environment Deployment

**Purpose**: Validate infrastructure provisioning in dev

**Procedure**:
1. Merge PR to main branch
2. Monitor "Deploy to Dev Environment" workflow
3. Verify successful deployment

**Manual Verification**:
```bash
# Login to Azure
az login
az account set --subscription "<dev-subscription-id>"

# Check Resource Group
az group show --name payments-ingestion-dev-rg

# Verify Event Hub
az eventhubs namespace show \
  --resource-group payments-ingestion-dev-rg \
  --name payments-ingestion-dev-evhns-eus

# Verify Function App
az functionapp show \
  --resource-group payments-ingestion-dev-rg \
  --name payments-ingestion-dev-func-eus

# Verify PostgreSQL
az postgres flexible-server show \
  --resource-group payments-ingestion-dev-rg \
  --name payments-ingestion-dev-psql-eus

# Verify Storage Account
az storage account show \
  --resource-group payments-ingestion-dev-rg \
  --name <storage-account-name>
```

**Pass Criteria**:
- All resources created successfully
- Resources match Terraform configuration
- No provisioning errors in workflow logs
- Resources are in "Running" or "Succeeded" state

### 2. Staging Environment Deployment

**Purpose**: Validate production-like deployment

**Procedure**:
1. Trigger "Deploy to Staging Environment" workflow
2. Approve deployment (if protection rules enabled)
3. Monitor deployment progress
4. Run smoke tests

**Pass Criteria**:
- Deployment completes successfully
- All resources provisioned
- Smoke tests pass
- Configuration matches staging requirements

### 3. Production Environment Deployment

**Purpose**: Validate production deployment process

⚠️ **Only perform with approval and during maintenance window**

**Procedure**:
1. Trigger "Deploy to Production Environment" workflow
2. Type "DEPLOY" to confirm
3. Approve deployment
4. Monitor deployment closely
5. Run health checks

**Pass Criteria**:
- Confirmation and approval required
- Deployment completes without errors
- Health checks pass
- Deployment tag created
- No degradation in service

## Database Schema Testing

### 1. Schema Deployment Test

**Purpose**: Validate database schema creation

**Procedure**:
```bash
# Set environment variables
export DATABASE_HOST="<server-fqdn>"
export DATABASE_NAME="payments_db"
export DATABASE_USER="psqladmin"
export DATABASE_PASSWORD="<password>"

# Run deployment script (dry run first)
export DRY_RUN="true"
./scripts/database/deploy-schema.sh dev

# Review output, then apply
export DRY_RUN="false"
./scripts/database/deploy-schema.sh dev
```

**Pass Criteria**:
- All schema files apply successfully
- No SQL errors
- Tables created with correct structure
- Indexes created
- Foreign keys established
- Views created successfully

### 2. Schema Validation Test

**Purpose**: Verify database schema completeness

**Procedure**:
```bash
# Run validation script
./scripts/database/validate-schema.sh

# Expected Output:
# ✅ Table 'normalizedtransactions' EXISTS
# ✅ Table 'dynamicmetrics' EXISTS
# ✅ Table 'payment_metrics_5m' EXISTS
# ✅ Foreign Key EXISTS
# ✅ Views EXIST
```

**Pass Criteria**:
- All required tables exist
- All indexes created
- Foreign key constraints present
- Views functional

## CI/CD Pipeline Testing

### 1. PR Workflow Test

**Purpose**: Validate pull request validation pipeline

**Test Cases**:
| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Valid Changes | Create PR with valid Terraform changes | ✅ All checks pass, plan succeeds |
| Invalid Syntax | Create PR with syntax error | ❌ Validation fails |
| Security Issue | Create PR with insecure config | ⚠️ Snyk reports issue |
| Multiple Environments | Change shared module | ✅ Plans run for all affected envs |

### 2. Deployment Workflow Test

**Test Cases**:
| Test Case | Environment | Steps | Expected Result |
|-----------|-------------|-------|-----------------|
| Auto Deploy | Dev | Merge to main | ✅ Automatically deploys |
| Manual Deploy | Staging | Trigger workflow manually | ✅ Deploys after approval |
| Confirmation Required | Production | Trigger without confirmation | ❌ Workflow fails |
| Confirmation Provided | Production | Type "DEPLOY" | ✅ Deploys after approval |

### 3. Database Deployment Workflow Test

**Test Cases**:
| Test Case | Steps | Expected Result |
|-----------|-------|-----------------|
| Dry Run | Set dry_run=true | ✅ Shows changes without applying |
| Dev Deployment | Deploy to dev, confirm "dev" | ✅ Schema applies successfully |
| Validation After Deploy | Run schema validation | ✅ All validations pass |

## Drift Detection Testing

**Purpose**: Verify infrastructure drift detection

**Procedure**:
```bash
# Check for drift in development
./scripts/check-drift.sh dev

# Make manual change in Azure Portal (test only!)
# Example: Change Event Hub retention period

# Run drift detection again
./scripts/check-drift.sh dev

# Expected: Drift detected and reported
```

**Pass Criteria**:
- No drift when infrastructure matches code
- Drift correctly detected when manual changes made
- Drift report shows accurate differences

## Rollback Testing

**Purpose**: Validate rollback capabilities

### Infrastructure Rollback

**Procedure**:
1. Note current deployment state
2. Deploy a change
3. Revert Git commit
4. Redeploy previous version

**Pass Criteria**:
- Previous state restored
- No data loss
- Resources return to previous configuration

### Database Rollback

**Procedure**:
1. Create backup before schema change
2. Apply schema change
3. Test rollback using backup restore

**Pass Criteria**:
- Backup restores successfully
- Data integrity maintained
- Application functions with restored schema

## Performance Testing

### Infrastructure Provisioning Time

**Metrics to Collect**:
| Environment | Target | Measurement |
|-------------|--------|-------------|
| Development | < 10 min | Time from workflow start to completion |
| Staging | < 15 min | Time from workflow start to completion |
| Production | < 20 min | Time from workflow start to completion |

### Database Schema Deployment

**Metrics to Collect**:
- Schema deployment time
- Validation time
- Connection establishment time

**Pass Criteria**:
- Dev deployment < 2 minutes
- Staging deployment < 3 minutes
- Production deployment < 5 minutes

## Security Testing

### 1. Secrets Management

**Test Cases**:
- ✅ Secrets not exposed in logs
- ✅ Secrets not committed to Git
- ✅ Separate secrets per environment
- ✅ Rotation process documented

### 2. Network Security

**Test Cases**:
- ✅ Storage accounts enforce HTTPS
- ✅ PostgreSQL requires SSL
- ✅ TLS 1.2 minimum enforced
- ✅ Firewall rules applied

### 3. Access Control

**Test Cases**:
- ✅ Service principals have least privilege
- ✅ Managed identities used where possible
- ✅ Different credentials per environment
- ✅ Production requires additional approvals

## Documentation Testing

### Accuracy Verification

**Procedure**:
1. Follow README instructions exactly
2. Follow Deployment Guide step-by-step
3. Test all code examples
4. Verify all links work

**Pass Criteria**:
- Instructions produce expected results
- No broken links
- Code examples execute successfully
- Screenshots/diagrams are current

### Completeness Check

**Required Documentation**:
- ✅ README.md
- ✅ iac/README.md
- ✅ docs/ARCHITECTURE.md
- ✅ docs/MODULE-REFERENCE.md
- ✅ docs/CI-CD-PIPELINE.md
- ✅ docs/DEPLOYMENT-GUIDE.md
- ✅ docs/ONBOARDING.md
- ✅ docs/TESTING-PROCEDURES.md (this document)
- ✅ docs/adr/*.md (5 ADRs)

## Test Results Documentation

### Test Execution Log Template

```markdown
## Test Execution: [Date]

**Tester**: [Name]
**Environment**: [Dev/Staging/Production]
**Build**: [Commit SHA]

### Pre-Deployment Tests
- [ ] Terraform Validation: PASS/FAIL
- [ ] Security Scan: PASS/FAIL
- [ ] PR Workflow: PASS/FAIL

### Deployment Tests
- [ ] Infrastructure Deployment: PASS/FAIL
- [ ] Database Schema: PASS/FAIL
- [ ] Resource Verification: PASS/FAIL

### Post-Deployment Tests
- [ ] Drift Detection: PASS/FAIL
- [ ] Documentation: PASS/FAIL

### Issues Found
[List any issues discovered]

### Notes
[Additional observations]
```

## Continuous Testing

### Weekly Tasks
- ✅ Run drift detection on all environments
- ✅ Verify backups are being created
- ✅ Review security scan results
- ✅ Check documentation accuracy

### Monthly Tasks
- ✅ Full deployment test in staging
- ✅ Performance baseline measurement
- ✅ Disaster recovery test
- ✅ Documentation review and update

## Test Automation

### Automated Tests (via CI/CD)
- Terraform format and validate
- Security scanning (Snyk)
- Terraform plan on PR
- Auto-deployment to dev
- Schema validation post-deployment

### Manual Tests (Required)
- Staging deployment approval
- Production deployment confirmation
- Resource verification in Azure Portal
- End-to-end workflow validation
- Documentation accuracy review

## Troubleshooting Test Failures

### Common Issues and Solutions

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| Terraform validation fails | Syntax error | Run `terraform fmt -recursive` |
| Deployment fails | Authentication error | Check Azure credentials/secrets |
| Resource already exists | Name conflict | Update resource names |
| State lock error | Concurrent operation | Wait or force-unlock |
| Schema deployment fails | Connection error | Verify network rules, credentials |

## Sign-Off

### Phase 1 Testing Completion Checklist

- [ ] All pre-deployment tests passed
- [ ] Dev environment deployed and verified
- [ ] Staging environment deployed and verified
- [ ] Production deployment process validated
- [ ] Database schemas deployed and validated
- [ ] CI/CD pipelines tested end-to-end
- [ ] Security configurations verified
- [ ] Documentation reviewed and accurate
- [ ] All test results documented
- [ ] Known issues documented with mitigation plans

**Approved By**: _________________  
**Date**: _________________  
**Role**: _________________

---

**Document Version**: 1.0  
**Last Updated**: December 2025  
**Maintained By**: Infrastructure Team

