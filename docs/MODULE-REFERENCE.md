# Terraform Module Reference

This document provides detailed API reference for all Terraform modules in the Payments Ingestion infrastructure.

## Table of Contents

1. [Event Hub Module](#event-hub-module)
2. [Function App Module](#function-app-module)
3. [PostgreSQL Module](#postgresql-module)
4. [Storage Account Module](#storage-account-module)

---

## Event Hub Module

**Path:** `iac/modules/event_hub/`

**Purpose:** Provisions Azure Event Hub Namespace, Event Hub, Consumer Groups, and authorization rules for message streaming.

### Resources Created

- `azurerm_eventhub_namespace` - Event Hub Namespace
- `azurerm_eventhub` - Event Hub instance
- `azurerm_eventhub_consumer_group` - Consumer groups (multiple)
- `azurerm_eventhub_authorization_rule` - Send and listen authorization rules

### Inputs

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `namespace_name` | string | Yes | - | Name of the Event Hub Namespace |
| `eventhub_name` | string | Yes | - | Name of the Event Hub |
| `location` | string | Yes | - | Azure region for deployment |
| `resource_group_name` | string | Yes | - | Name of the resource group |
| `sku` | string | No | `"Standard"` | SKU tier (Basic, Standard, Premium) |
| `capacity` | number | No | `1` | Throughput units (1-20) |
| `auto_inflate_enabled` | bool | No | `false` | Enable auto-inflate for throughput units |
| `maximum_throughput_units` | number | No | `20` | Max throughput units when auto-inflate is enabled |
| `partition_count` | number | No | `2` | Number of partitions (1-32) |
| `message_retention` | number | No | `1` | Message retention in days (1-7) |
| `consumer_groups` | list(string) | No | `["default"]` | List of consumer group names |
| `tags` | map(string) | No | `{}` | Resource tags |

### Outputs

| Name | Type | Sensitive | Description |
|------|------|-----------|-------------|
| `namespace_id` | string | No | ID of the Event Hub Namespace |
| `namespace_name` | string | No | Name of the Event Hub Namespace |
| `eventhub_id` | string | No | ID of the Event Hub |
| `eventhub_name` | string | No | Name of the Event Hub |
| `primary_connection_string` | string | Yes | Primary connection string for namespace |
| `secondary_connection_string` | string | Yes | Secondary connection string for namespace |
| `send_connection_string` | string | Yes | Connection string with send permissions |
| `listen_connection_string` | string | Yes | Connection string with listen permissions |
| `consumer_groups` | map | No | Map of consumer group names to IDs |

### Usage Example

```hcl
module "event_hub" {
  source = "../../modules/event_hub"

  namespace_name      = "my-eventhub-namespace"
  eventhub_name       = "my-eventhub"
  location            = "East US"
  resource_group_name = azurerm_resource_group.main.name

  sku                      = "Standard"
  capacity                 = 2
  partition_count          = 4
  message_retention        = 3
  auto_inflate_enabled     = true
  maximum_throughput_units = 10

  consumer_groups = [
    "default",
    "payment-processor",
    "analytics"
  ]

  tags = {
    Environment = "production"
    Project     = "payments"
  }
}
```

### Best Practices

1. **Partition Count:** Choose based on expected throughput (1 partition ≈ 1 MB/s ingress)
2. **Consumer Groups:** Create separate groups for independent consumers
3. **Auto-Inflate:** Enable for production workloads with variable traffic
4. **Retention:** Balance cost vs. replay requirements (1-7 days)
5. **Authorization:** Use separate send/listen rules for least privilege

---

## Function App Module

**Path:** `iac/modules/function_app/`

**Purpose:** Provisions Azure Function App with App Service Plan and associated storage for serverless compute.

### Resources Created

- `azurerm_storage_account` - Storage account for function app
- `azurerm_service_plan` - App Service Plan (Linux)
- `azurerm_linux_function_app` - Linux Function App

### Inputs

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `function_app_name` | string | Yes | - | Name of the Function App |
| `app_service_plan_name` | string | Yes | - | Name of the App Service Plan |
| `storage_account_name` | string | Yes | - | Name of storage account (3-24 chars, lowercase/numbers only) |
| `storage_replication_type` | string | No | `"LRS"` | Storage replication type (LRS, GRS, RAGRS, ZRS, GZRS, RAGZRS) |
| `location` | string | Yes | - | Azure region for deployment |
| `resource_group_name` | string | Yes | - | Name of the resource group |
| `sku_name` | string | No | `"Y1"` | SKU for App Service Plan (Y1=Consumption, EP1/EP2/EP3=Premium) |
| `python_version` | string | No | `"3.11"` | Python runtime version (3.8, 3.9, 3.10, 3.11) |
| `always_on` | bool | No | `false` | Keep function app always on (not for Consumption) |
| `app_settings` | map(string) | No | `{}` | Additional application settings |
| `application_insights_key` | string | No | `null` | Application Insights instrumentation key |
| `application_insights_connection_string` | string | No | `null` | Application Insights connection string |
| `tags` | map(string) | No | `{}` | Resource tags |

### Outputs

| Name | Type | Sensitive | Description |
|------|------|-----------|-------------|
| `function_app_id` | string | No | ID of the Function App |
| `function_app_name` | string | No | Name of the Function App |
| `function_app_default_hostname` | string | No | Default hostname of the Function App |
| `function_app_identity_principal_id` | string | No | Principal ID of managed identity |
| `function_app_identity_tenant_id` | string | No | Tenant ID of managed identity |
| `app_service_plan_id` | string | No | ID of the App Service Plan |
| `storage_account_id` | string | No | ID of the storage account |
| `storage_account_name` | string | No | Name of the storage account |
| `storage_account_primary_connection_string` | string | Yes | Primary connection string for storage |

### Usage Example

```hcl
module "function_app" {
  source = "../../modules/function_app"

  function_app_name        = "my-function-app"
  app_service_plan_name    = "my-app-service-plan"
  storage_account_name     = "myfuncappstorage"
  storage_replication_type = "GRS"
  location                 = "East US"
  resource_group_name      = azurerm_resource_group.main.name

  sku_name       = "EP1"  # Premium plan
  python_version = "3.11"
  always_on      = true

  app_settings = {
    "EVENTHUB_CONNECTION_STRING" = module.event_hub.listen_connection_string
    "LOG_LEVEL"                  = "INFO"
  }

  tags = {
    Environment = "production"
    Project     = "payments"
  }
}
```

### Best Practices

1. **Plan Selection:**
   - Use Consumption (Y1) for dev/test with variable workloads
   - Use Premium (EP1/EP2) for production requiring always-on or VNet integration
2. **Storage Account:** Choose appropriate replication based on criticality
3. **App Settings:** Pass connection strings and configuration via app_settings
4. **Managed Identity:** Use output principal_id to grant resource access
5. **Always On:** Required for premium plans to avoid cold starts

---

## PostgreSQL Module

**Path:** `iac/modules/postgresql/`

**Purpose:** Provisions Azure Database for PostgreSQL Flexible Server with databases, firewall rules, and configurations.

### Resources Created

- `azurerm_postgresql_flexible_server` - PostgreSQL Flexible Server
- `azurerm_postgresql_flexible_server_database` - Databases (multiple)
- `azurerm_postgresql_flexible_server_firewall_rule` - Firewall rules (multiple)
- `azurerm_postgresql_flexible_server_configuration` - Server configurations (multiple)

### Inputs

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `server_name` | string | Yes | - | Name of the PostgreSQL server |
| `location` | string | Yes | - | Azure region for deployment |
| `resource_group_name` | string | Yes | - | Name of the resource group |
| `postgresql_version` | string | No | `"14"` | PostgreSQL version (11, 12, 13, 14, 15) |
| `administrator_login` | string | Yes | - | Administrator username |
| `administrator_password` | string | Yes | - | Administrator password (sensitive) |
| `sku_name` | string | No | `"B_Standard_B1ms"` | SKU name (e.g., B_Standard_B1ms, GP_Standard_D2s_v3) |
| `storage_mb` | number | No | `32768` | Storage capacity in MB (32768-16777216) |
| `backup_retention_days` | number | No | `7` | Backup retention period (7-35 days) |
| `geo_redundant_backup_enabled` | bool | No | `false` | Enable geo-redundant backups |
| `high_availability_mode` | string | No | `"Disabled"` | HA mode (Disabled, ZoneRedundant, SameZone) |
| `database_names` | list(string) | No | `["payments_db"]` | List of database names to create |
| `database_charset` | string | No | `"UTF8"` | Database charset |
| `database_collation` | string | No | `"en_US.utf8"` | Database collation |
| `allow_azure_services` | bool | No | `true` | Allow Azure services to access server |
| `firewall_rules` | map(object) | No | `{}` | Map of firewall rules {name = {start_ip, end_ip}} |
| `postgresql_configurations` | map(string) | No | `{}` | Map of PostgreSQL parameters {name = value} |
| `tags` | map(string) | No | `{}` | Resource tags |

### Outputs

| Name | Type | Sensitive | Description |
|------|------|-----------|-------------|
| `server_id` | string | No | ID of the PostgreSQL server |
| `server_name` | string | No | Name of the PostgreSQL server |
| `server_fqdn` | string | No | Fully qualified domain name of the server |
| `administrator_login` | string | Yes | Administrator username |
| `database_ids` | map | No | Map of database names to IDs |
| `database_names` | list | No | List of created database names |
| `connection_string` | string | Yes | PostgreSQL connection string |

### Usage Example

```hcl
module "postgresql" {
  source = "../../modules/postgresql"

  server_name         = "my-postgresql-server"
  location            = "East US"
  resource_group_name = azurerm_resource_group.main.name

  postgresql_version     = "14"
  administrator_login    = "psqladmin"
  administrator_password = var.postgresql_admin_password

  sku_name   = "GP_Standard_D2s_v3"
  storage_mb = 65536  # 64 GB

  backup_retention_days        = 14
  geo_redundant_backup_enabled = true
  high_availability_mode       = "ZoneRedundant"

  database_names = [
    "payments_db",
    "analytics_db"
  ]

  allow_azure_services = true

  firewall_rules = {
    "office_ip" = {
      start_ip = "203.0.113.10"
      end_ip   = "203.0.113.10"
    }
  }

  postgresql_configurations = {
    "max_connections" = "200"
    "shared_buffers"  = "256MB"
  }

  tags = {
    Environment = "production"
    Project     = "payments"
  }
}
```

### Best Practices

1. **SKU Selection:**
   - Burstable (B_*): Dev/test workloads
   - General Purpose (GP_*): Production workloads
   - Memory Optimized (MO_*): High-memory requirements
2. **High Availability:** Enable ZoneRedundant for production
3. **Backups:** Use geo-redundant backups for critical data
4. **Firewall:** Minimize exposed IP ranges, use Private Endpoints when possible
5. **Parameters:** Tune based on workload (connections, memory, cache)

---

## Storage Account Module

**Path:** `iac/modules/storage_account/`

**Purpose:** Provisions Azure Storage Account with containers, queues, tables, and network rules.

### Resources Created

- `azurerm_storage_account` - Storage Account
- `azurerm_storage_container` - Blob containers (multiple)
- `azurerm_storage_queue` - Queues (multiple)
- `azurerm_storage_table` - Tables (multiple)
- `azurerm_storage_account_network_rules` - Network security rules (optional)

### Inputs

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `storage_account_name` | string | Yes | - | Name (3-24 chars, lowercase/numbers only) |
| `location` | string | Yes | - | Azure region for deployment |
| `resource_group_name` | string | Yes | - | Name of the resource group |
| `account_tier` | string | No | `"Standard"` | Account tier (Standard, Premium) |
| `replication_type` | string | No | `"LRS"` | Replication type (LRS, GRS, RAGRS, ZRS, GZRS, RAGZRS) |
| `account_kind` | string | No | `"StorageV2"` | Account kind (BlobStorage, BlockBlobStorage, FileStorage, Storage, StorageV2) |
| `allow_public_access` | bool | No | `false` | Allow public blob access |
| `enable_versioning` | bool | No | `true` | Enable blob versioning |
| `enable_change_feed` | bool | No | `false` | Enable blob change feed |
| `delete_retention_days` | number | No | `7` | Blob soft delete retention (1-365 days) |
| `container_delete_retention_days` | number | No | `7` | Container soft delete retention (1-365 days) |
| `container_names` | list(string) | No | `[]` | List of container names to create |
| `container_access_type` | string | No | `"private"` | Container access level (private, blob, container) |
| `queue_names` | list(string) | No | `[]` | List of queue names to create |
| `table_names` | list(string) | No | `[]` | List of table names to create |
| `enable_network_rules` | bool | No | `false` | Enable network security rules |
| `default_network_action` | string | No | `"Deny"` | Default network action (Allow, Deny) |
| `network_bypass` | list(string) | No | `["AzureServices"]` | Services that bypass network rules |
| `ip_rules` | list(string) | No | `[]` | List of allowed IP addresses/CIDR blocks |
| `virtual_network_subnet_ids` | list(string) | No | `[]` | List of allowed VNet subnet IDs |
| `tags` | map(string) | No | `{}` | Resource tags |

### Outputs

| Name | Type | Sensitive | Description |
|------|------|-----------|-------------|
| `storage_account_id` | string | No | ID of the Storage Account |
| `storage_account_name` | string | No | Name of the Storage Account |
| `primary_blob_endpoint` | string | No | Primary blob service endpoint |
| `primary_queue_endpoint` | string | No | Primary queue service endpoint |
| `primary_table_endpoint` | string | No | Primary table service endpoint |
| `primary_access_key` | string | Yes | Primary access key |
| `secondary_access_key` | string | Yes | Secondary access key |
| `primary_connection_string` | string | Yes | Primary connection string |
| `secondary_connection_string` | string | Yes | Secondary connection string |
| `identity_principal_id` | string | No | Principal ID of managed identity |
| `container_ids` | map | No | Map of container names to IDs |
| `queue_ids` | map | No | Map of queue names to IDs |
| `table_ids` | map | No | Map of table names to IDs |

### Usage Example

```hcl
module "storage_account" {
  source = "../../modules/storage_account"

  storage_account_name = "mypaymentsstorage"
  location             = "East US"
  resource_group_name  = azurerm_resource_group.main.name

  account_tier       = "Standard"
  replication_type   = "GZRS"
  account_kind       = "StorageV2"
  allow_public_access = false

  enable_versioning                = true
  enable_change_feed               = true
  delete_retention_days            = 30
  container_delete_retention_days  = 30

  container_names = [
    "payments-data",
    "processed-payments",
    "archives",
    "audit-logs"
  ]

  queue_names = [
    "payment-processing-queue",
    "error-queue",
    "dlq"
  ]

  table_names = [
    "audit-table"
  ]

  enable_network_rules    = true
  default_network_action  = "Deny"
  network_bypass          = ["AzureServices"]
  ip_rules                = ["203.0.113.0/24"]

  tags = {
    Environment = "production"
    Project     = "payments"
  }
}
```

### Best Practices

1. **Replication:**
   - LRS: Dev/test
   - GRS/GZRS: Production critical data
   - ZRS: Production within region
2. **Security:**
   - Disable public access
   - Enable network rules for production
   - Use managed identity for access
3. **Data Protection:**
   - Enable versioning for critical blobs
   - Configure appropriate retention periods
   - Use lifecycle management for archival
4. **Naming:** Names must be globally unique and lowercase
5. **Monitoring:** Enable diagnostic logs and metrics

---

## Common Patterns

### Passing Module Outputs

```hcl
# Use Event Hub output in Function App
module "function_app" {
  source = "../../modules/function_app"
  # ... other config ...
  
  app_settings = {
    "EVENTHUB_CONNECTION" = module.event_hub.listen_connection_string
    "STORAGE_CONNECTION"  = module.storage_account.primary_connection_string
    "DATABASE_HOST"       = module.postgresql.server_fqdn
  }
}
```

### Using Tags Consistently

```hcl
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

module "event_hub" {
  source = "../../modules/event_hub"
  # ... other config ...
  tags = local.common_tags
}
```

### Managed Identity Access

```hcl
# Grant Function App access to Storage Account
resource "azurerm_role_assignment" "function_to_storage" {
  scope                = module.storage_account.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = module.function_app.function_app_identity_principal_id
}
```

---

**Document Version:** 1.0  
**Last Updated:** December 2025  
**Maintained By:** Infrastructure Team

