# Payments Ingestion Infrastructure

Azure-based infrastructure for ingesting and processing payment data using Event Hubs, Azure Functions, and PostgreSQL.

## 📁 Repository Structure

```
payments-ingestion/
├── .github/
│   └── workflows/           # GitHub Actions CI/CD workflows
│       ├── reusable-terraform.yml
│       ├── terraform-plan.yml
│       ├── terraform-deploy-dev.yml
│       ├── terraform-deploy-staging.yml
│       ├── terraform-deploy-production.yml
│       └── terraform-destroy.yml
├── iac/                    # Infrastructure as Code
│   ├── modules/           # Reusable Terraform modules
│   │   ├── event_hub/
│   │   ├── function_app/
│   │   ├── postgresql/
│   │   └── storage_account/
│   └── environments/      # Environment-specific configs
│       ├── dev/
│       ├── staging/
│       └── production/
├── scripts/               # Helper scripts
│   ├── validate-terraform.sh
│   ├── check-drift.sh
│   ├── setup-github-secrets.sh
│   └── terraform-plan-summary.sh
├── docs/                  # Documentation
│   ├── CI-CD-PIPELINE.md
│   └── DEPLOYMENT-GUIDE.md
└── .terraform-version     # Terraform version pinning
```

## 🚀 Quick Start

### Prerequisites

- Azure subscription(s)
- Azure CLI installed
- Terraform 1.6.0+
- GitHub repository access

### Initial Setup

1. **Create Azure Service Principals**
   ```bash
   ./scripts/setup-github-secrets.sh
   ```

2. **Configure GitHub Secrets**
   - Follow the guide in `docs/DEPLOYMENT-GUIDE.md`
   - Add all required secrets to GitHub repository settings

3. **Deploy Infrastructure**
   ```bash
   # Automatically deploys to dev when you merge to main
   git checkout -b feature/initial-setup
   git add .
   git commit -m "Initial infrastructure setup"
   git push origin feature/initial-setup
   # Create PR and merge
   ```

## 📚 Documentation

### Infrastructure & Deployment
- **[Deployment Guide](docs/DEPLOYMENT-GUIDE.md)** - Complete deployment procedures
- **[CI/CD Pipeline](docs/CI-CD-PIPELINE.md)** - Pipeline architecture and workflows
- **[IaC README](iac/README.md)** - Infrastructure as Code documentation

### Payment Data Simulator
- **[Simulator User Guide](docs/SIMULATOR-USER-GUIDE.md)** - Complete user documentation
- **[Simulator README](src/simulator/README.md)** - Quick start guide
- **[Configuration Example](config/simulator_config.yaml.example)** - Example configuration file

## 🏗️ Infrastructure Components

### Azure Resources

- **Event Hub** - Message streaming for payment data ingestion
- **Azure Functions** - Serverless payment processing
- **PostgreSQL** - Persistent storage for processed payments
- **Storage Account** - Blob storage for data and function app storage

### Environments

- **Development** - Auto-deploy on merge to main
- **Staging** - Manual deployment with smoke tests
- **Production** - Manual deployment with approval gates

## 🔧 Helper Scripts

```bash
# Validate all Terraform configurations
./scripts/validate-terraform.sh

# Check for infrastructure drift
./scripts/check-drift.sh dev

# Setup GitHub secrets (guide)
./scripts/setup-github-secrets.sh

# Generate plan summary
./scripts/terraform-plan-summary.sh tfplan
```

## 🔄 Deployment Workflow

1. **Development**
   - Create feature branch
   - Make infrastructure changes
   - Open Pull Request
   - Review Terraform plan
   - Merge → Auto-deploys to dev

2. **Staging**
   - Go to Actions → Deploy to Staging
   - Click "Run workflow"
   - Review and approve

3. **Production**
   - Go to Actions → Deploy to Production
   - Type "DEPLOY" to confirm
   - Review and approve

## 🔐 Security

- ✅ Snyk IaC security scanning on all PRs
- ✅ TLS 1.2 enforced on all resources
- ✅ Managed identities for Azure resources
- ✅ Separate service principals per environment
- ✅ Geo-redundant storage in staging/production
- ✅ Encrypted secrets in GitHub

## 📊 Cost Estimates

| Environment | Monthly Cost (Est.) |
|-------------|-------------------|
| Development | ~$35-80 |
| Staging | ~$200-400 |
| Production | ~$450-900 |

## 🆘 Support & Troubleshooting

See [Deployment Guide - Troubleshooting](docs/DEPLOYMENT-GUIDE.md#troubleshooting) for common issues and solutions.

## 📝 Contributing

1. Create feature branch from `main`
2. Make changes to IaC
3. Run `./scripts/validate-terraform.sh`
4. Create Pull Request
5. Review Terraform plan in PR comments
6. Merge after approval

## 🔗 Additional Resources

- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure CLI Reference](https://docs.microsoft.com/en-us/cli/azure/)
- [GitHub Actions](https://docs.github.com/en/actions)

## 📜 License

Copyright © 2025 Payments Ingestion Project

---

**Version:** 1.0  
**Last Updated:** December 2025

