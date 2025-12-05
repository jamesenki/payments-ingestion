# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records (ADRs) for the Payments Ingestion project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences.

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](./001-use-terraform-for-iac.md) | Use Terraform for Infrastructure as Code | Accepted | 2025-12-04 |
| [ADR-002](./002-azure-event-hubs-for-ingestion.md) | Use Azure Event Hubs for Message Ingestion | Accepted | 2025-12-04 |
| [ADR-003](./003-github-actions-for-cicd.md) | Use GitHub Actions for CI/CD | Accepted | 2025-12-04 |
| [ADR-004](./004-postgresql-flexible-server.md) | Use Azure PostgreSQL Flexible Server | Accepted | 2025-12-04 |
| [ADR-005](./005-multi-environment-strategy.md) | Multi-Environment Deployment Strategy | Accepted | 2025-12-04 |

## ADR Template

When creating a new ADR, use this template:

```markdown
# ADR-XXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
What is the issue that we're seeing that is motivating this decision or change?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?

### Positive
- Benefit 1
- Benefit 2

### Negative
- Drawback 1
- Drawback 2

## Alternatives Considered
What other options were evaluated?

## References
- Link 1
- Link 2
```

