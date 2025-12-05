# New Team Member Onboarding Guide

Welcome to the Payments Ingestion project! This guide will help you get started with the codebase, tools, and workflows.

## 🎯 Overview

The Payments Ingestion system is a cloud-native Azure-based platform for processing payment transactions in real-time. You'll be working with:
- **Infrastructure as Code** (Terraform)
- **CI/CD Pipelines** (GitHub Actions)
- **Cloud Services** (Azure Event Hubs, Functions, PostgreSQL)
- **Python** (for application development - Phase 2)

## 📋 Prerequisites Checklist

Before you begin, ensure you have:

### Required Tools
- [ ] **Git** - Version control
  ```bash
  git --version
  ```
- [ ] **Azure CLI** - Azure command-line tool
  ```bash
  az --version
  # If not installed: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
  ```
- [ ] **Terraform** - Infrastructure as code
  ```bash
  terraform version
  # Should be 1.6.0 or higher
  ```
- [ ] **Code Editor** - VS Code recommended with extensions:
  - Terraform
  - Azure Terraform
  - YAML
  - Python

### Required Access
- [ ] **GitHub** - Repository access
- [ ] **Azure Portal** - Access to dev subscription
- [ ] **Azure AD** - Company account setup
- [ ] **Snyk** - Security scanning account (optional)

## 🚀 Day 1: Getting Started

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone <repository-url>
cd payments-ingestion

# Check the repository structure
ls -la
```

### Step 2: Authenticate with Azure

```bash
# Login to Azure
az login

# List available subscriptions
az account list --output table

# Set the dev subscription as default
az account set --subscription "<dev-subscription-id>"

# Verify current subscription
az account show
```

### Step 3: Explore the Codebase

```
payments-ingestion/
├── .github/workflows/     # CI/CD pipelines
├── docs/                  # Documentation (you are here!)
├── iac/                   # Infrastructure as Code
│   ├── modules/          # Terraform modules
│   └── environments/     # Environment configs
├── scripts/               # Helper scripts
└── README.md             # Project overview
```

### Step 4: Read the Documentation

Recommended reading order:
1. ✅ `README.md` - Project overview
2. ✅ `docs/ARCHITECTURE.md` - System design
3. ✅ `docs/MODULE-REFERENCE.md` - Terraform modules
4. ✅ `docs/CI-CD-PIPELINE.md` - Pipeline details
5. ✅ `docs/DEPLOYMENT-GUIDE.md` - Deployment procedures

### Step 5: Run Local Validation

```bash
# Validate Terraform configurations
./scripts/validate-terraform.sh

# Check the output for any errors
```

## 📚 Day 2-3: Understand the System

### System Components

1. **Infrastructure Layer (Phase 1 - Complete)**
   - Event Hub for message streaming
   - Azure Functions for processing
   - PostgreSQL for data storage
   - Storage Account for archives

2. **Application Layer (Phase 2 - Upcoming)**
   - Data simulator for testing
   - Azure Functions for processing
   - Metric calculation engine

3. **CI/CD Layer (Phase 1 - Complete)**
   - GitHub Actions workflows
   - Automated testing
   - Multi-environment deployment

### Key Concepts

**Terraform Modules:**
- Reusable infrastructure components
- Located in `iac/modules/`
- Event Hub, Function App, PostgreSQL, Storage Account

**Environments:**
- **Dev**: Auto-deploy, for development
- **Staging**: Manual deploy, for testing
- **Production**: Manual deploy with approval, for live traffic

**CI/CD Workflows:**
- **PR Validation**: terraform-plan.yml
- **Dev Deployment**: terraform-deploy-dev.yml
- **Staging Deployment**: terraform-deploy-staging.yml
- **Production Deployment**: terraform-deploy-production.yml

## 🛠️ Day 3-5: Your First Contribution

### Task 1: Make a Small Change

Let's start with a simple change to get familiar with the workflow:

```bash
# 1. Create a feature branch
git checkout -b feature/my-first-change

# 2. Make a small change (e.g., update a comment in a Terraform file)
vim iac/environments/dev/main.tf
# Add a comment like: # Updated by [Your Name]

# 3. Validate your change
./scripts/validate-terraform.sh

# 4. Commit and push
git add .
git commit -m "docs: Add comment to dev environment config"
git push origin feature/my-first-change

# 5. Create a Pull Request on GitHub
# - Go to repository on GitHub
# - Click "Compare & pull request"
# - Fill in description
# - Submit for review
```

### Task 2: Review the Terraform Plan

When your PR is created:
1. GitHub Actions will automatically run
2. Check the "Terraform Plan" workflow
3. Review the plan output in PR comments
4. Verify no unexpected changes

### Task 3: Deploy to Dev (after merge)

```bash
# After PR is merged, deployment happens automatically to dev
# Monitor the deployment:
# 1. Go to GitHub Actions tab
# 2. Find "Deploy to Dev Environment" workflow
# 3. Watch the logs
```

## 🎓 Week 1-2: Deep Dive Topics

### Topic 1: Terraform Modules

**Exercise:** Understand the Event Hub module
1. Read `iac/modules/event_hub/main.tf`
2. List all resources created
3. Identify inputs and outputs
4. Trace how it's used in `iac/environments/dev/main.tf`

**Questions to answer:**
- What parameters control the Event Hub capacity?
- How many consumer groups are created?
- How are connection strings exposed?

### Topic 2: CI/CD Pipelines

**Exercise:** Understand the deployment flow
1. Read `.github/workflows/terraform-plan.yml`
2. Understand the trigger conditions
3. Trace the workflow steps
4. Find where secrets are used

**Questions to answer:**
- When does the plan workflow run?
- How are multiple environments handled?
- What happens if validation fails?

### Topic 3: Azure Resources

**Exercise:** Explore Azure Portal
1. Login to Azure Portal
2. Find the dev resource group
3. Explore each resource (Event Hub, PostgreSQL, etc.)
4. Check metrics and logs

**Questions to answer:**
- What is the current throughput of Event Hub?
- How many databases exist in PostgreSQL?
- What containers are in the Storage Account?

## 🔧 Common Development Tasks

### Running Terraform Locally

```bash
# Navigate to environment directory
cd iac/environments/dev

# Initialize Terraform
terraform init

# Plan changes
terraform plan

# Apply changes (dev only - be careful!)
terraform apply

# Note: For staging/prod, always use CI/CD pipelines
```

### Checking for Drift

```bash
# Check if deployed infrastructure matches code
./scripts/check-drift.sh dev

# Review the drift report
cat iac/environments/dev/drift-report.txt
```

### Testing Configuration Changes

```bash
# 1. Make changes to Terraform files
# 2. Validate syntax
terraform fmt -recursive
terraform validate

# 3. Run validation script
./scripts/validate-terraform.sh

# 4. Create PR to see plan output
```

### Debugging Pipeline Failures

```bash
# 1. Check GitHub Actions logs
# 2. Look for error messages
# 3. Common issues:
#    - Authentication failures → Check secrets
#    - State lock issues → Wait or force-unlock
#    - Resource conflicts → Check Azure Portal
#    - Validation errors → Run validation script locally
```

## 📖 Reference Materials

### Internal Documentation
- [Architecture](./ARCHITECTURE.md) - System design
- [Module Reference](./MODULE-REFERENCE.md) - Terraform modules API
- [CI/CD Pipeline](./CI-CD-PIPELINE.md) - Pipeline details
- [Deployment Guide](./DEPLOYMENT-GUIDE.md) - How to deploy
- [Troubleshooting](./DEPLOYMENT-GUIDE.md#troubleshooting) - Common issues

### External Resources
- [Terraform Azure Provider Docs](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure Event Hubs Docs](https://docs.microsoft.com/azure/event-hubs/)
- [Azure Functions Docs](https://docs.microsoft.com/azure/azure-functions/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

## 🤝 Team Workflows

### Daily Standup
- Share what you worked on yesterday
- Share what you'll work on today
- Raise any blockers

### Code Review Process
1. Create feature branch from `main`
2. Make changes
3. Run validation scripts
4. Create Pull Request
5. Request review from 1-2 team members
6. Address feedback
7. Get approval
8. Merge to `main`

### Deployment Process
1. **Dev**: Auto-deploys on merge to `main`
2. **Staging**: Manual workflow dispatch after testing in dev
3. **Production**: Manual workflow with approval after staging validation

### Getting Help
- **Technical Questions**: Ask in team Slack channel
- **Azure Issues**: Check Azure Portal health status
- **Pipeline Issues**: Check GitHub Actions logs
- **Urgent Issues**: Contact on-call engineer

## ✅ Onboarding Checklist

### Week 1
- [ ] Development environment setup complete
- [ ] Repository cloned and explored
- [ ] All documentation read
- [ ] First PR created and merged
- [ ] Understand CI/CD workflow
- [ ] Know how to run Terraform locally

### Week 2
- [ ] Understand all Terraform modules
- [ ] Can explain system architecture
- [ ] Deployed a change to dev environment
- [ ] Reviewed someone else's PR
- [ ] Comfortable with Git workflow
- [ ] Know where to find logs and metrics

### Week 3
- [ ] Made a meaningful contribution
- [ ] Deployed to staging environment
- [ ] Participated in code review
- [ ] Troubleshot a pipeline failure
- [ ] Understand monitoring and alerts
- [ ] Ready for independent work

### Week 4
- [ ] Working independently on tasks
- [ ] Mentoring others through onboarding
- [ ] Contributing to documentation
- [ ] Participating in design discussions
- [ ] Full team member!

## 🎉 Welcome to the Team!

You're now ready to contribute to the Payments Ingestion project. Remember:

1. **Ask Questions** - No question is too small
2. **Read Documentation** - It's here to help you
3. **Use PRs** - Don't commit directly to main
4. **Test Locally** - Validate before pushing
5. **Review Code** - Learn from others' changes
6. **Have Fun** - Building cloud infrastructure is exciting!

## 📞 Contacts

| Role | Name | Contact |
|------|------|---------|
| Tech Lead | TBD | - |
| DevOps Lead | TBD | - |
| Infrastructure | TBD | - |
| On-Call | Rotation | Check schedule |

---

**Questions?** Reach out in the team Slack channel or create a GitHub Discussion.

**Found an error in this guide?** Create a PR to fix it - documentation PRs are always welcome!

**Good luck and happy coding! 🚀**

