# Production Environment Configuration

project_name        = "payments-ingestion"
environment         = "production"
location            = "East US"
resource_group_name = "payments-ingestion-prod-rg"
cost_center         = "payments"

# Event Hub Configuration
eventhub_sku                     = "Standard"
eventhub_capacity                = 4
eventhub_partition_count         = 8
eventhub_message_retention       = 7
eventhub_auto_inflate_enabled    = true
eventhub_maximum_throughput_units = 20
eventhub_consumer_groups         = ["default", "payments-processor", "analytics", "monitoring", "audit"]

# Storage Account Configuration
storage_account_tier     = "Standard"
storage_replication_type = "GZRS"
storage_container_names  = ["raw-events", "payments-data", "processed-payments", "archives", "audit-logs", "backups"]
storage_queue_names      = ["payment-processing-queue", "error-queue", "retry-queue", "dlq"]
storage_table_names      = []

# Function App Configuration
function_app_sku            = "EP2"
function_app_python_version = "3.11"
function_app_always_on      = true
function_app_settings = {
  "LOG_LEVEL"                 = "WARNING"
  "ENABLE_PERFORMANCE_METRICS" = "true"
  "ENABLE_TELEMETRY"          = "true"
}

# PostgreSQL Configuration
postgresql_version                = "14"
postgresql_admin_login            = "psqladmin"
# CRITICAL: postgresql_admin_password MUST be provided via environment variable or Azure Key Vault
# Example: export TF_VAR_postgresql_admin_password="YourVerySecurePassword123!"
# DO NOT store production passwords in terraform.tfvars
postgresql_sku                    = "GP_Standard_D4s_v3"
postgresql_storage_mb             = 131072
postgresql_backup_retention_days  = 35
postgresql_geo_redundant_backup   = true
postgresql_high_availability_mode = "ZoneRedundant"
postgresql_database_names         = ["payments_db"]

# PostgreSQL Firewall Rules (Optional - add specific IPs as needed)
# NOTE: For production, consider using Private Endpoints instead of firewall rules
postgresql_firewall_rules = {
  # "office_ip" = {
  #   start_ip = "1.2.3.4"
  #   end_ip   = "1.2.3.4"
  # }
}

