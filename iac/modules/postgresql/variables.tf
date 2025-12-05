variable "server_name" {
  description = "The name of the PostgreSQL server"
  type        = string
}

variable "location" {
  description = "The Azure region where the PostgreSQL server will be created"
  type        = string
}

variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "postgresql_version" {
  description = "The version of PostgreSQL to use"
  type        = string
  default     = "14"
  validation {
    condition     = contains(["11", "12", "13", "14", "15"], var.postgresql_version)
    error_message = "PostgreSQL version must be 11, 12, 13, 14, or 15."
  }
}

variable "administrator_login" {
  description = "The administrator login for the PostgreSQL server"
  type        = string
}

variable "administrator_password" {
  description = "The administrator password for the PostgreSQL server"
  type        = string
  sensitive   = true
}

variable "sku_name" {
  description = "The SKU name for the PostgreSQL server (e.g., B_Standard_B1ms, GP_Standard_D2s_v3)"
  type        = string
  default     = "B_Standard_B1ms"
}

variable "storage_mb" {
  description = "The storage capacity in MB for the PostgreSQL server"
  type        = number
  default     = 32768
  validation {
    condition     = var.storage_mb >= 32768 && var.storage_mb <= 16777216
    error_message = "Storage must be between 32GB (32768 MB) and 16TB (16777216 MB)."
  }
}

variable "backup_retention_days" {
  description = "The number of days to retain backups"
  type        = number
  default     = 7
  validation {
    condition     = var.backup_retention_days >= 7 && var.backup_retention_days <= 35
    error_message = "Backup retention must be between 7 and 35 days."
  }
}

variable "geo_redundant_backup_enabled" {
  description = "Enable geo-redundant backups"
  type        = bool
  default     = false
}

variable "high_availability_mode" {
  description = "High availability mode (Disabled, ZoneRedundant, SameZone)"
  type        = string
  default     = "Disabled"
  validation {
    condition     = contains(["Disabled", "ZoneRedundant", "SameZone"], var.high_availability_mode)
    error_message = "High availability mode must be Disabled, ZoneRedundant, or SameZone."
  }
}

variable "database_names" {
  description = "List of database names to create"
  type        = list(string)
  default     = ["payments_db"]
}

variable "database_charset" {
  description = "The charset for the database"
  type        = string
  default     = "UTF8"
}

variable "database_collation" {
  description = "The collation for the database"
  type        = string
  default     = "en_US.utf8"
}

variable "allow_azure_services" {
  description = "Allow Azure services to access the PostgreSQL server"
  type        = bool
  default     = true
}

variable "firewall_rules" {
  description = "Map of firewall rules to create"
  type = map(object({
    start_ip = string
    end_ip   = string
  }))
  default = {}
}

variable "postgresql_configurations" {
  description = "Map of PostgreSQL configuration parameters"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Tags to apply to the PostgreSQL resources"
  type        = map(string)
  default     = {}
}

