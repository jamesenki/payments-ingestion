# Infrastructure as Code (IaC) for Payments Ingestion

This directory contains Terraform scripts for provisioning Azure resources for the Payments Ingestion system.

## Overview

The infrastructure is organized into modular components that can be deployed across multiple environments (dev, staging, production).

### Resources Provisioned

- **Event Hub**: For streaming payment data ingestion
- **Function App**: For processing payment events
- **PostgreSQL Database**: For storing processed payment data
- **Storage Account**: For blob storage and function app storage needs

## Prerequisites

Before using these Terraform scripts, ensure you have:

1. **Terraform** installed (version 1.0 or higher)
   ```bash
   terraform version
   ```

2. **Azure CLI** installed and authenticated
   ```bash
   az login
   az account show
   ```

3. **Azure Subscription** with appropriate permissions to create resources

4. **Backend Configuration** (optional but recommended for team collaboration)
   - Configure remote state storage in Azure Storage Account

## Project Structure

```
iac/
├── README.md                      # This file
├── main.tf                        # Root-level provider configuration
├── variables.tf                   # Global variables
├── outputs.tf                     # Global outputs
├── naming_conventions.tf          # Naming standards and tagging
├── modules/                       # Reusable resource modules
│   ├── event_hub/                # Event Hub module
│   ├── function_app/             # Function App module
│   ├── postgresql/               # PostgreSQL module
│   └── storage_account/          # Storage Account module
└── environments/                  # Environment-specific configurations
    ├── dev/                      # Development environment
    ├── staging/                  # Staging environment
    └── production/               # Production environment
```

## Usage

### 1. Initialize Terraform

Navigate to the desired environment directory and initialize Terraform:

```bash
cd environments/dev
terraform init
```

### 2. Review the Plan

Review the resources that will be created:

```bash
terraform plan
```

### 3. Apply the Configuration

Deploy the infrastructure:

```bash
terraform apply
```

### 4. Destroy Resources (when needed)

To tear down the infrastructure:

```bash
terraform destroy
```

## Environment-Specific Deployment

### Development Environment

```bash
cd environments/dev
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

### Staging Environment

```bash
cd environments/staging
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

### Production Environment

```bash
cd environments/production
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

## Variable Configuration

Each environment has its own `terraform.tfvars` file containing environment-specific values:

- Resource names and prefixes
- SKU/tier selections
- Capacity and scaling configurations
- Network and security settings

**Important**: Sensitive values (passwords, connection strings) should be:
- Stored in Azure Key Vault
- Passed as environment variables
- Never committed to version control

## Naming Conventions

All resources follow a consistent naming pattern defined in `naming_conventions.tf`:

```
{project}-{environment}-{resource_type}-{region}
```

Example: `payments-dev-eventhub-eastus`

## Tagging Strategy

All resources are tagged with:
- `Environment`: dev, staging, production
- `Project`: payments-ingestion
- `ManagedBy`: terraform
- `CostCenter`: (as appropriate)

## Modules

### Event Hub Module

Provisions Event Hub Namespace, Event Hub, and Consumer Groups for event streaming.

### Function App Module

Creates Function App with App Service Plan and associated storage for serverless processing.

### PostgreSQL Module

Deploys Azure Database for PostgreSQL server and databases for data persistence.

### Storage Account Module

Creates Storage Account with containers for blob storage needs.

## Security Best Practices

- Use managed identities where possible
- Enable encryption at rest and in transit
- Configure network security rules and private endpoints
- Regularly rotate credentials
- Enable diagnostic logging

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   az login
   az account set --subscription <subscription-id>
   ```

2. **State Lock Issues**
   ```bash
   terraform force-unlock <lock-id>
   ```

3. **Resource Name Conflicts**
   - Ensure resource names are globally unique (especially Storage Accounts)
   - Check `terraform.tfvars` for naming conflicts

## Additional Resources

- [Terraform Azure Provider Documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Azure Event Hubs Documentation](https://docs.microsoft.com/azure/event-hubs/)
- [Azure Functions Documentation](https://docs.microsoft.com/azure/azure-functions/)
- [Azure PostgreSQL Documentation](https://docs.microsoft.com/azure/postgresql/)

## Support

For questions or issues related to this infrastructure:
- Review the implementation plan in the work order
- Check Azure resource documentation
- Contact the platform team

