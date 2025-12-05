# Staging Environment Configuration

project_name        = "payments-ingestion"
environment         = "staging"
location            = "East US"
resource_group_name = "payments-ingestion-staging-rg"

# Event Hub Configuration
eventhub_sku                     = "Standard"
eventhub_capacity                = 2
eventhub_partition_count         = 4
eventhub_message_retention       = 3
eventhub_auto_inflate_enabled    = true
eventhub_maximum_throughput_units = 10
eventhub_consumer_groups         = ["default", "payments-processor", "analytics", "monitoring"]

# Storage Account Configuration
storage_account_tier     = "Standard"
storage_replication_type = "GRS"
storage_container_names  = ["payments-data", "processed-payments", "archives", "audit-logs"]
storage_queue_names      = ["payment-processing-queue", "error-queue", "retry-queue"]
storage_table_names      = []

# Function App Configuration
function_app_sku            = "EP1"
function_app_python_version = "3.11"
function_app_always_on      = true
function_app_settings = {
  "LOG_LEVEL" = "INFO"
}

# PostgreSQL Configuration
postgresql_version                = "14"
postgresql_admin_login            = "psqladmin"
# Note: postgresql_admin_password should be provided via environment variable or secure method
# Example: export TF_VAR_postgresql_admin_password="YourSecurePassword123!"
postgresql_sku                    = "GP_Standard_D2s_v3"
postgresql_storage_mb             = 65536
postgresql_backup_retention_days  = 14
postgresql_geo_redundant_backup   = true
postgresql_high_availability_mode = "ZoneRedundant"
postgresql_database_names         = ["payments_db"]

# PostgreSQL Firewall Rules (Optional - add specific IPs as needed)
postgresql_firewall_rules = {
  # "office_ip" = {
  #   start_ip = "1.2.3.4"
  #   end_ip   = "1.2.3.4"
  # }
}

