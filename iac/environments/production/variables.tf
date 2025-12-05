variable "project_name" {
  description = "The name of the project"
  type        = string
  default     = "payments-ingestion"
}

variable "environment" {
  description = "The environment name"
  type        = string
  default     = "production"
}

variable "location" {
  description = "The Azure region for resources"
  type        = string
  default     = "East US"
}

variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "payments"
}

# Event Hub Variables
variable "eventhub_sku" {
  description = "The SKU of the Event Hub Namespace"
  type        = string
  default     = "Standard"
}

variable "eventhub_capacity" {
  description = "The capacity of the Event Hub Namespace"
  type        = number
  default     = 4
}

variable "eventhub_partition_count" {
  description = "The number of partitions for the Event Hub"
  type        = number
  default     = 8
}

variable "eventhub_message_retention" {
  description = "The number of days to retain messages"
  type        = number
  default     = 7
}

variable "eventhub_auto_inflate_enabled" {
  description = "Enable auto-inflate for Event Hub"
  type        = bool
  default     = true
}

variable "eventhub_maximum_throughput_units" {
  description = "Maximum throughput units for auto-inflate"
  type        = number
  default     = 20
}

variable "eventhub_consumer_groups" {
  description = "List of consumer groups"
  type        = list(string)
  default     = ["default", "payments-processor"]
}

# Storage Account Variables
variable "storage_account_tier" {
  description = "The tier of the Storage Account"
  type        = string
  default     = "Standard"
}

variable "storage_replication_type" {
  description = "The replication type for the Storage Account"
  type        = string
  default     = "GZRS"
}

variable "storage_container_names" {
  description = "List of storage container names"
  type        = list(string)
  default     = ["payments-data", "processed-payments"]
}

variable "storage_queue_names" {
  description = "List of storage queue names"
  type        = list(string)
  default     = ["payment-processing-queue"]
}

variable "storage_table_names" {
  description = "List of storage table names"
  type        = list(string)
  default     = []
}

# Function App Variables
variable "function_app_sku" {
  description = "The SKU for the App Service Plan"
  type        = string
  default     = "EP2"
}

variable "function_app_python_version" {
  description = "The Python version for the Function App"
  type        = string
  default     = "3.11"
}

variable "function_app_always_on" {
  description = "Should the Function App be always on"
  type        = bool
  default     = true
}

variable "function_app_settings" {
  description = "Additional app settings for the Function App"
  type        = map(string)
  default     = {}
}

# PostgreSQL Variables
variable "postgresql_version" {
  description = "The version of PostgreSQL"
  type        = string
  default     = "14"
}

variable "postgresql_admin_login" {
  description = "The administrator login for PostgreSQL"
  type        = string
  sensitive   = true
}

variable "postgresql_admin_password" {
  description = "The administrator password for PostgreSQL"
  type        = string
  sensitive   = true
}

variable "postgresql_sku" {
  description = "The SKU for PostgreSQL"
  type        = string
  default     = "GP_Standard_D4s_v3"
}

variable "postgresql_storage_mb" {
  description = "The storage capacity in MB"
  type        = number
  default     = 131072
}

variable "postgresql_backup_retention_days" {
  description = "The number of days to retain backups"
  type        = number
  default     = 35
}

variable "postgresql_geo_redundant_backup" {
  description = "Enable geo-redundant backups"
  type        = bool
  default     = true
}

variable "postgresql_high_availability_mode" {
  description = "High availability mode"
  type        = string
  default     = "ZoneRedundant"
}

variable "postgresql_database_names" {
  description = "List of database names"
  type        = list(string)
  default     = ["payments_db"]
}

variable "postgresql_firewall_rules" {
  description = "Map of firewall rules"
  type = map(object({
    start_ip = string
    end_ip   = string
  }))
  default = {}
}

