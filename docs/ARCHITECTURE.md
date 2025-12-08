# Payments Ingestion System Architecture

## Overview

The Payments Ingestion system is a cloud-native, event-driven architecture built on Azure services for processing and analyzing payment transaction data in real-time.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Payment Data Sources                        │
│              (External Systems, APIs, Partners)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Payment Transactions
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Simulator (Optional)                     │
│                  Python Application (Phase 2)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Simulated Transactions
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Azure Event Hubs                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Namespace: payments-ingestion-{env}-evhns-eus           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Event Hub: payments-ingestion-{env}-evh-eus       │  │  │
│  │  │  - Partitions: 2-8 (env dependent)                 │  │  │
│  │  │  - Retention: 1-7 days                             │  │  │
│  │  │  - Consumer Groups: default, processor, analytics  │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Event Triggers
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Azure Functions (Phase 2)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Function App: payments-ingestion-{env}-func-eus         │  │
│  │  - Runtime: Python 3.11                                  │  │
│  │  - Hosting: Consumption (dev) / Premium (staging/prod)  │  │
│  │  - Triggers: Event Hub, Timer                           │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Functions:                                         │ │  │
│  │  │  1. Normalize Transactions                         │ │  │
│  │  │  2. Calculate Dynamic Metrics                      │ │  │
│  │  │  3. Aggregate 5-minute Metrics                     │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Writes Data
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Hybrid Storage Architecture                          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Azure Blob Storage (Raw Events)                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Container: raw-events                              │  │  │
│  │  │  Format: Parquet files                              │  │  │
│  │  │  Partition: yyyy={year}/mm={month}/dd={day}/       │  │  │
│  │  │  Lifecycle: Hot → Cool → Archive                    │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Azure Database for PostgreSQL (Metrics)                 │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Server: payments-ingestion-{env}-psql-eus           │  │  │
│  │  │  Database: payments_db                               │  │  │
│  │  │  Tables:                                            │  │  │
│  │  │  1. dynamic_metrics (per-transaction metrics)      │  │  │
│  │  │  2. payment_metrics_5m (5-min aggregates)         │  │  │
│  │  │  3. aggregate_histograms (distribution data)       │  │  │
│  │  │  4. failed_items (dead-letter queue)               │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │
                         │ Analytics & Reporting
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Storage Account                               │
│  - Blob Storage (raw events)                                    │
│  - Archives                                                      │
│  - Audit Logs                                                    │
│  - Backups                                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Azure Event Hubs (Ingestion Layer)

**Purpose:** High-throughput message streaming service for payment transaction ingestion

**Key Features:**
- **Namespace:** Isolated messaging container
- **Event Hub:** Stream endpoint for payment events
- **Partitions:** Enable parallel processing (2-8 based on environment)
- **Consumer Groups:** Allow multiple independent consumers
- **Retention:** Configurable message retention (1-7 days)

**Configuration by Environment:**
| Feature | Dev | Staging | Production |
|---------|-----|---------|------------|
| SKU | Standard | Standard | Standard |
| Capacity (TUs) | 1 | 2 | 4 |
| Partitions | 2 | 4 | 8 |
| Retention | 1 day | 3 days | 7 days |
| Auto-inflate | Disabled | Enabled | Enabled |

**Security:**
- Managed Identity authentication
- SAS token-based authorization
- Network rules and firewall
- Encryption at rest and in transit

### 2. Azure Functions (Processing Layer)

**Purpose:** Serverless compute for event-driven payment processing

**Key Features:**
- **Event Hub Trigger:** Automatically processes incoming events
- **Timer Trigger:** Scheduled metric aggregation
- **Python Runtime:** v3.11 for modern Python features
- **Managed Identity:** Secure access to Azure resources

**Configuration by Environment:**
| Feature | Dev | Staging | Production |
|---------|-----|---------|------------|
| Plan | Consumption (Y1) | Premium (EP1) | Premium (EP2) |
| Always On | No | Yes | Yes |
| Storage | LRS | GRS | GZRS |
| Auto-scale | No | Yes | Yes |

**Functions (Phase 2):**
1. **Transaction Normalizer** - Validates and standardizes payment data
2. **Metric Calculator** - Computes dynamic business metrics
3. **Aggregator** - Creates 5-minute time-series summaries

### 3. Hybrid Storage Architecture

**Purpose:** Efficient storage strategy combining Blob Storage for raw events and PostgreSQL for processed metrics

#### 3.1 Azure Blob Storage (Raw Events)

**Purpose:** High-volume, cost-effective storage for raw transaction events

**Key Features:**
- **Parquet Format:** Columnar storage optimized for analytics
- **Partitioning:** Date-based folder structure (`yyyy={year}/mm={month}/dd={day}/`)
- **Lifecycle Management:** Automated tiering (Hot → Cool → Archive) and retention policies
- **Cost Efficiency:** Significantly cheaper than PostgreSQL for large volumes
- **Scalability:** Scales to petabytes without performance degradation

**Configuration by Environment:**
| Feature | Dev | Staging | Production |
|---------|-----|---------|------------|
| Container | raw-events | raw-events | raw-events |
| Hot Tier Retention | 7 days | 7 days | 7 days |
| Cool Tier Retention | 30 days | 30 days | 30 days |
| Archive Tier Retention | 90 days | 180 days | 365 days |
| Compression | Snappy | Snappy | Snappy |

**Storage Structure:**
```
raw-events/
├── yyyy=2025/
│   ├── mm=12/
│   │   ├── dd=07/
│   │   │   ├── events_20251207_000000.parquet
│   │   │   ├── events_20251207_010000.parquet
│   │   │   └── ...
```

#### 3.2 Azure Database for PostgreSQL (Metrics)

**Purpose:** Relational database for processed metrics and aggregates

**Key Features:**
- **Flexible Server:** Latest PostgreSQL deployment option
- **High Availability:** Zone-redundant configuration
- **Automated Backups:** Daily with point-in-time restore
- **Connection Pooling:** Efficient connection management

**Configuration by Environment:**
| Feature | Dev | Staging | Production |
|---------|-----|---------|------------|
| SKU | B_Standard_B1ms | GP_Standard_D2s_v3 | GP_Standard_D4s_v3 |
| Storage | 32 GB | 64 GB | 128 GB |
| Backup Retention | 7 days | 14 days | 35 days |
| HA Mode | Disabled | ZoneRedundant | ZoneRedundant |
| Geo-Redundant | No | Yes | Yes |

**Database Schema:**
```
payments_db
├── dynamic_metrics (per-transaction metrics)
│   ├── metric_id (PK)
│   ├── transaction_id
│   ├── correlation_id (UUID)
│   ├── metric_type
│   ├── metric_value
│   ├── metric_data (JSONB)
│   └── created_at
│
├── payment_metrics_5m (5-minute aggregates)
│   ├── window_start (PK)
│   ├── window_end
│   ├── total_count
│   ├── total_amount
│   ├── avg_amount
│   ├── payment_method_breakdown (JSONB)
│   └── currency_breakdown (JSONB)
│
├── aggregate_histograms (distribution data)
│   ├── histogram_id (PK)
│   ├── window_start
│   ├── metric_type
│   ├── histogram_data (JSONB)
│   └── created_at
│
└── failed_items (dead-letter queue)
    ├── failed_id (PK)
    ├── transaction_id
    ├── error_type
    ├── error_message
    ├── raw_payload (JSONB)
    └── failed_at
```

**Note:** Raw transaction events are stored in Blob Storage as Parquet files, not in PostgreSQL. See [ADR-006](./adr/006-hybrid-storage-architecture.md) for architectural rationale.

### 4. Storage Account (Support Layer)

**Purpose:** Blob storage for archives, logs, and function app storage

**Key Features:**
- **Containers:** Logical blob storage separation
- **Queues:** Asynchronous message processing
- **Versioning:** Point-in-time recovery
- **Lifecycle Management:** Automated data tiering

**Configuration by Environment:**
| Feature | Dev | Staging | Production |
|---------|-----|---------|------------|
| Replication | LRS | GRS | GZRS |
| Tier | Standard | Standard | Standard |
| TLS Version | 1.2 | 1.2 | 1.2 |
| Retention | 7 days | 14 days | 30 days |

**Containers:**
- `raw-events` - Raw transaction events (Parquet files) - **Primary storage for normalized transactions**
- `processed-payments` - Processed data exports
- `archives` - Long-term storage
- `audit-logs` - Compliance and audit trails
- `backups` - Database backup files

## Data Flow

### 1. Ingestion Flow

```
External Source → Event Hub → Consumer Group → Function Trigger
```

**Steps:**
1. Payment transaction sent to Event Hub
2. Event persisted across partitions for durability
3. Consumer group tracks processing offset
4. Azure Function triggered with batched events

### 2. Processing Flow

```
Function Trigger → Normalize → Validate → Transform → Store
```

**Steps:**
1. Function receives event batch
2. Normalize transaction structure
3. Validate against business rules
4. Transform and enrich data
5. Store raw event to Blob Storage (Parquet)
6. Calculate and store metrics to PostgreSQL

### 3. Metrics Flow

```
Raw Event (Blob Storage) → Extract → Calculate Metrics → Aggregate → Store (PostgreSQL)
```

**Steps:**
1. Read raw event from Blob Storage (or from processing pipeline)
2. Extract transaction data
3. Apply metric derivation rules
4. Calculate dynamic metrics (store in `dynamic_metrics` table)
5. Aggregate into time windows (store in `payment_metrics_5m` table)
6. Generate histograms (store in `aggregate_histograms` table)

## Network Architecture

### Virtual Network Configuration (Future Enhancement)

```
┌─────────────────────────────────────────────────────┐
│  Azure Virtual Network: payments-vnet               │
│  Address Space: 10.0.0.0/16                         │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  Subnet: function-subnet (10.0.1.0/24)        │ │
│  │  - Azure Functions VNet Integration           │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │  Subnet: data-subnet (10.0.2.0/24)            │ │
│  │  - PostgreSQL Private Endpoint                │ │
│  │  - Event Hub Private Endpoint                 │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Current:** Public endpoints with firewall rules
**Future:** Private endpoints for enhanced security

## Security Architecture

### Identity and Access Management

```
┌──────────────────────────────────────────────────┐
│  Azure Active Directory                          │
│  ┌────────────────────────────────────────────┐  │
│  │  Service Principals (CI/CD)                │  │
│  │  - Dev SP: Contributor on dev subscription │  │
│  │  - Staging SP: Contributor on staging sub  │  │
│  │  - Prod SP: Contributor on prod sub        │  │
│  └────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │  Managed Identities (Runtime)              │  │
│  │  - Function App Identity                   │  │
│  │  - Storage Account Identity                │  │
│  │  - Event Hub Identity                      │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Secret Management

**Current Approach:**
- GitHub Secrets for CI/CD credentials
- Environment variables for function app configuration
- Connection strings in app settings

**Future Enhancement (Phase 3):**
- Azure Key Vault for all secrets
- Managed Identity authentication to Key Vault
- Secret rotation automation

### Data Encryption

**At Rest:**
- Storage Account: Microsoft-managed keys
- PostgreSQL: Transparent Data Encryption (TDE)
- Event Hub: Server-side encryption

**In Transit:**
- TLS 1.2+ for all connections
- HTTPS only for function endpoints
- SSL required for PostgreSQL connections

## Scalability & Performance

### Scaling Strategy

**Event Hubs:**
- Auto-inflate enabled (staging/production)
- Partition scaling for parallel processing
- Throughput units scale with load

**Azure Functions:**
- Consumption: Auto-scale 0 to 200 instances (dev)
- Premium: Pre-warmed instances, faster scaling (staging/prod)
- Event Hub trigger batch size tuning

**PostgreSQL:**
- Vertical scaling: SKU upgrades
- Connection pooling: PgBouncer integration
- Read replicas: For analytics workloads (future)

### Performance Targets

| Metric | Dev | Staging | Production |
|--------|-----|---------|------------|
| Ingestion Rate | 100 events/sec | 1,000 events/sec | 10,000 events/sec |
| Processing Latency | < 5 sec | < 2 sec | < 1 sec |
| Storage Latency | < 500 ms | < 200 ms | < 100 ms |
| Availability | 95% | 99% | 99.9% |

## Disaster Recovery

### Backup Strategy

**PostgreSQL:**
- Automated daily backups
- Point-in-time restore (7-35 days)
- Geo-redundant backup storage (staging/prod)

**Storage Account:**
- Geo-redundant replication (staging/prod)
- Zone-redundant replication (prod)
- Soft delete enabled (7-30 days)

**Event Hub:**
- No backup (stream processing pattern)
- Message retention for replay (1-7 days)

### Recovery Procedures

**RTO (Recovery Time Objective):**
- Dev: 4 hours
- Staging: 1 hour
- Production: 15 minutes

**RPO (Recovery Point Objective):**
- Dev: 24 hours
- Staging: 1 hour
- Production: 5 minutes

## Monitoring & Observability

### Metrics Collection (Future)

```
Azure Monitor
├── Application Insights
│   ├── Function App telemetry
│   ├── Request tracking
│   ├── Exception logging
│   └── Performance counters
│
├── Log Analytics
│   ├── Event Hub metrics
│   ├── PostgreSQL logs
│   ├── Storage analytics
│   └── Security logs
│
└── Alerts
    ├── High error rates
    ├── Slow query performance
    ├── Resource exhaustion
    └── Security events
```

### Key Metrics to Monitor

**Application:**
- Event processing rate
- Function execution time
- Error rates and exceptions
- Database query performance

**Infrastructure:**
- CPU and memory utilization
- Storage capacity
- Network throughput
- Service health status

## Cost Optimization

### Cost Breakdown (Monthly Estimates)

**Development:**
- Event Hub: $10-20
- Functions: $0-10
- PostgreSQL: $20-40
- Storage: $5-10
- **Total: ~$35-80/month**

**Production:**
- Event Hub: $80-150
- Functions: $150-300
- PostgreSQL: $200-400
- Storage: $20-50
- **Total: ~$450-900/month**

### Optimization Strategies

1. **Right-size resources** based on actual usage
2. **Use consumption plan** for variable workloads
3. **Implement auto-scaling** to avoid over-provisioning
4. **Archive old data** to cheaper storage tiers
5. **Use reserved instances** for predictable workloads

## Technology Stack

### Infrastructure
- **IaC**: Terraform 1.6.0
- **Cloud Provider**: Microsoft Azure
- **Regions**: East US (primary)

### Application (Phase 2)
- **Language**: Python 3.11
- **Framework**: Azure Functions Runtime v4
- **Database**: PostgreSQL 14
- **Messaging**: Azure Event Hubs

### CI/CD
- **Platform**: GitHub Actions
- **Security Scanning**: Snyk
- **Testing**: pytest (Phase 2)

## Future Enhancements

### Phase 2 (Application Development)
- Implement data simulator
- Develop Azure Functions
- Create database schemas
- Build metric engine

### Phase 3 (Advanced Features)
- Azure Key Vault integration
- Private endpoints and VNet integration
- Advanced monitoring and alerting
- Read replicas for analytics
- Data archival automation

### Phase 4 (Optimization)
- Machine learning integration
- Advanced analytics
- Real-time dashboards
- Anomaly detection
- Cost optimization automation

---

**Document Version:** 1.0  
**Last Updated:** December 2025  
**Maintained By:** Infrastructure Team

