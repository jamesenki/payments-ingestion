# Development Environment Configuration

project_name        = "payments-ingestion"
environment         = "dev"
location            = "East US"
resource_group_name = "payments-ingestion-dev-rg"

# Event Hub Configuration
eventhub_sku                     = "Standard"
eventhub_capacity                = 1
eventhub_partition_count         = 2
eventhub_message_retention       = 1
eventhub_auto_inflate_enabled    = false
eventhub_maximum_throughput_units = 20
eventhub_consumer_groups         = ["default", "payments-processor", "analytics"]

# Storage Account Configuration
storage_account_tier     = "Standard"
storage_replication_type = "LRS"
storage_container_names  = ["payments-data", "processed-payments", "archives"]
storage_queue_names      = ["payment-processing-queue", "error-queue"]
storage_table_names      = []

# Function App Configuration
function_app_sku            = "Y1"
function_app_python_version = "3.11"
function_app_always_on      = false
function_app_settings = {
  "LOG_LEVEL" = "DEBUG"
}

# PostgreSQL Configuration
postgresql_version                = "14"
postgresql_admin_login            = "psqladmin"
# Note: postgresql_admin_password should be provided via environment variable or secure method
# Example: export TF_VAR_postgresql_admin_password="YourSecurePassword123!"
postgresql_sku                    = "B_Standard_B1ms"
postgresql_storage_mb             = 32768
postgresql_backup_retention_days  = 7
postgresql_geo_redundant_backup   = false
postgresql_high_availability_mode = "Disabled"
postgresql_database_names         = ["payments_db"]

# PostgreSQL Firewall Rules (Optional - add specific IPs as needed)
postgresql_firewall_rules = {
  # "office_ip" = {
  #   start_ip = "1.2.3.4"
  #   end_ip   = "1.2.3.4"
  # }
}

