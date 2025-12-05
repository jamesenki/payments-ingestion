# ADR-001: Use Terraform for Infrastructure as Code

## Status
Accepted

## Context
The Payments Ingestion system requires infrastructure provisioning across multiple Azure services (Event Hubs, Functions, PostgreSQL, Storage). We need a way to:
- Define infrastructure declaratively
- Support multiple environments (dev, staging, production)
- Enable version control and code review for infrastructure changes
- Provide consistent and repeatable deployments
- Support team collaboration

Options considered: Terraform, Azure Bicep, ARM Templates, Pulumi

## Decision
We will use **Terraform** with the Azure Provider (azurerm) as our Infrastructure as Code tool.

## Consequences

### Positive
- **Multi-cloud capability**: While we're using Azure now, Terraform provides flexibility to expand to other clouds if needed
- **Mature ecosystem**: Large community, extensive documentation, proven in production
- **State management**: Built-in state management with locking support
- **Module system**: Reusable modules for Event Hub, Function App, PostgreSQL, Storage Account
- **Provider maturity**: Azure provider is well-maintained and feature-complete
- **Declarative syntax**: HCL is readable and expressive
- **Plan before apply**: Terraform plan provides safety before making changes
- **Team familiarity**: Team has existing Terraform experience

### Negative
- **State file management**: Requires careful management of state files (mitigated with remote backend)
- **Learning curve**: New team members need to learn HCL syntax
- **Provider lag**: Sometimes Azure features take time to appear in Terraform provider
- **State drift**: Must monitor for manual changes made outside Terraform

## Alternatives Considered

### Azure Bicep
**Pros**: Native Azure tool, no state file, type safety
**Cons**: Azure-only, less mature than Terraform, smaller community
**Reason rejected**: Terraform's multi-cloud capability and maturity outweighed Bicep's advantages

### ARM Templates
**Pros**: Native Azure, no additional tools needed
**Cons**: JSON syntax is verbose and error-prone, poor developer experience
**Reason rejected**: Poor readability and maintainability

### Pulumi
**Pros**: Use familiar programming languages (Python, TypeScript)
**Cons**: Smaller community, less mature, team lacks experience
**Reason rejected**: Team familiarity with Terraform was prioritized

## Implementation Details

### Module Structure
```
iac/
├── modules/           # Reusable modules
│   ├── event_hub/
│   ├── function_app/
│   ├── postgresql/
│   └── storage_account/
└── environments/      # Environment-specific configs
    ├── dev/
    ├── staging/
    └── production/
```

### State Management
- Use Azure Storage backend for remote state
- Enable state locking to prevent concurrent modifications
- Separate state files per environment

### Version
- Terraform 1.6.0+
- Azure Provider ~> 3.0

## References
- [Terraform Azure Provider Documentation](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [Azure Bicep vs Terraform Comparison](https://docs.microsoft.com/azure/azure-resource-manager/bicep/compare-template-syntax)

## Date
2025-12-04

## Author
Infrastructure Team

