# ADR-005: Multi-Environment Deployment Strategy

## Status
Accepted

## Context
The Payments Ingestion system must support multiple deployment environments for different stages of the software lifecycle. We need to:
- Enable safe development and testing
- Provide production-like staging environment
- Ensure production stability and security
- Balance cost with capability
- Support parallel feature development

Requirements:
- Clear separation between environments
- Progressive deployment strategy
- Cost optimization for non-production environments
- Production-grade reliability for live traffic

## Decision
We will implement a **three-environment strategy**: Development, Staging, and Production, with distinct configurations and deployment processes for each.

## Consequences

### Positive
- **Risk reduction**: Changes tested in dev and staging before production
- **Cost optimization**: Lower-tier resources in dev/staging
- **Parallel development**: Multiple teams can work independently in dev
- **Production confidence**: Staging as production dress rehearsal
- **Clear promotion path**: dev → staging → production
- **Flexible testing**: Can test with realistic loads in staging

### Negative
- **Infrastructure cost**: Three full stacks to maintain
- **Configuration drift**: Risk of environment differences
- **Deployment complexity**: Multiple deployment processes to manage
- **Time to production**: Changes must pass through multiple stages

## Environment Specifications

### Development Environment

**Purpose**: Feature development and integration testing

**Characteristics**:
- Lowest cost configuration
- Auto-deploy on merge to main
- Frequent deployments (multiple per day)
- May be unstable during development
- Test data only

**Resource Configuration**:
```yaml
Event Hub:
  SKU: Standard
  Capacity: 1 TU
  Partitions: 2
  Retention: 1 day

Function App:
  Plan: Consumption (Y1)
  Always On: false

PostgreSQL:
  SKU: B_Standard_B1ms
  Storage: 32 GB
  HA: Disabled
  Backups: 7 days

Storage:
  Replication: LRS
```

**Deployment**: Automatic via GitHub Actions on merge to `main`

### Staging Environment

**Purpose**: Pre-production validation and performance testing

**Characteristics**:
- Production-like configuration at lower scale
- Manual deployment with approval
- Stable environment for QA testing
- Simulated production load testing
- Anonymized production-like data

**Resource Configuration**:
```yaml
Event Hub:
  SKU: Standard
  Capacity: 2 TU
  Partitions: 4
  Retention: 3 days
  Auto-inflate: enabled (max 10 TU)

Function App:
  Plan: Premium (EP1)
  Always On: true

PostgreSQL:
  SKU: GP_Standard_D2s_v3
  Storage: 64 GB
  HA: ZoneRedundant
  Backups: 14 days
  Geo-redundant: Yes

Storage:
  Replication: GRS
```

**Deployment**: Manual workflow dispatch with approval gate

### Production Environment

**Purpose**: Live customer traffic

**Characteristics**:
- Highest reliability and performance
- Manual deployment with confirmation
- Strict change control
- 24/7 monitoring and alerting
- Real customer data

**Resource Configuration**:
```yaml
Event Hub:
  SKU: Standard
  Capacity: 4 TU
  Partitions: 8
  Retention: 7 days
  Auto-inflate: enabled (max 20 TU)

Function App:
  Plan: Premium (EP2)
  Always On: true
  Pre-warmed instances: 2

PostgreSQL:
  SKU: GP_Standard_D4s_v3
  Storage: 128 GB
  HA: ZoneRedundant
  Backups: 35 days
  Geo-redundant: Yes

Storage:
  Replication: GZRS
```

**Deployment**: Manual workflow with typed confirmation ("DEPLOY") and approval

## Deployment Flow

```
┌─────────────┐
│Feature      │
│Branch       │
└──────┬──────┘
       │
       │ PR with Terraform Plan
       ▼
┌─────────────┐
│Code Review  │
│+ Plan Review│
└──────┬──────┘
       │
       │ Merge
       ▼
┌─────────────┐
│Development  │ ← Auto Deploy
│Environment  │
└──────┬──────┘
       │
       │ Manual Trigger
       ▼
┌─────────────┐
│Staging      │ ← Manual Deploy + Approval
│Environment  │
└──────┬──────┘
       │
       │ Manual Trigger + Confirmation
       ▼
┌─────────────┐
│Production   │ ← Manual Deploy + Confirmation + Approval
│Environment  │
└─────────────┘
```

## Environment Isolation

### Azure Subscriptions
- **Development**: Shared development subscription
- **Staging**: Shared non-production subscription
- **Production**: Dedicated production subscription

### Resource Groups
- Separate resource group per environment
- Naming: `payments-ingestion-{env}-rg`

### Network Isolation
- Public endpoints with firewall rules (Phase 1)
- Private endpoints and VNet integration (Future Phase)

### Access Control
- Separate service principals per environment
- Different GitHub secrets per environment
- Production requires additional approvals

## Cost Optimization

### Development
- Use consumption plans where possible
- Single-instance deployments
- Minimal retention periods
- LRS replication
- **Estimated Monthly Cost**: $35-80

### Staging
- Right-sized for testing loads
- Balance between cost and production similarity
- GRS replication for testing DR procedures
- **Estimated Monthly Cost**: $200-400

### Production
- Sized for expected production load
- High availability enabled
- Maximum backup retention
- GZRS replication for maximum durability
- **Estimated Monthly Cost**: $450-900

## Testing Strategy

| Test Type | Development | Staging | Production |
|-----------|------------|---------|------------|
| Unit Tests | ✅ | ✅ | N/A |
| Integration Tests | ✅ | ✅ | N/A |
| Smoke Tests | ✅ | ✅ | ✅ (post-deploy) |
| Load Tests | ❌ | ✅ | N/A |
| Security Scans | ✅ | ✅ | ✅ |

## Monitoring and Alerts

- **Development**: Basic monitoring, no alerts
- **Staging**: Full monitoring, warning alerts
- **Production**: Full monitoring, critical alerts, on-call escalation

## References
- [Azure Resource Organization Best Practices](https://docs.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming)
- [Environment Strategy Patterns](https://docs.microsoft.com/azure/architecture/framework/devops/deployment-patterns)

## Date
2025-12-04

## Author
Infrastructure Team

