variable "storage_account_name" {
  description = "The name of the Storage Account"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "Storage account name must be 3-24 characters, lowercase letters and numbers only."
  }
}

variable "location" {
  description = "The Azure region where the Storage Account will be created"
  type        = string
}

variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "account_tier" {
  description = "The tier of the Storage Account (Standard or Premium)"
  type        = string
  default     = "Standard"
  validation {
    condition     = contains(["Standard", "Premium"], var.account_tier)
    error_message = "Account tier must be Standard or Premium."
  }
}

variable "replication_type" {
  description = "The replication type for the Storage Account (LRS, GRS, RAGRS, ZRS, GZRS, RAGZRS)"
  type        = string
  default     = "LRS"
  validation {
    condition     = contains(["LRS", "GRS", "RAGRS", "ZRS", "GZRS", "RAGZRS"], var.replication_type)
    error_message = "Replication type must be LRS, GRS, RAGRS, ZRS, GZRS, or RAGZRS."
  }
}

variable "account_kind" {
  description = "The kind of Storage Account (BlobStorage, BlockBlobStorage, FileStorage, Storage, StorageV2)"
  type        = string
  default     = "StorageV2"
  validation {
    condition     = contains(["BlobStorage", "BlockBlobStorage", "FileStorage", "Storage", "StorageV2"], var.account_kind)
    error_message = "Account kind must be BlobStorage, BlockBlobStorage, FileStorage, Storage, or StorageV2."
  }
}

variable "allow_public_access" {
  description = "Allow public access to blobs"
  type        = bool
  default     = false
}

variable "enable_versioning" {
  description = "Enable blob versioning"
  type        = bool
  default     = true
}

variable "enable_change_feed" {
  description = "Enable blob change feed"
  type        = bool
  default     = false
}

variable "delete_retention_days" {
  description = "Number of days to retain deleted blobs"
  type        = number
  default     = 7
  validation {
    condition     = var.delete_retention_days >= 1 && var.delete_retention_days <= 365
    error_message = "Delete retention days must be between 1 and 365."
  }
}

variable "container_delete_retention_days" {
  description = "Number of days to retain deleted containers"
  type        = number
  default     = 7
  validation {
    condition     = var.container_delete_retention_days >= 1 && var.container_delete_retention_days <= 365
    error_message = "Container delete retention days must be between 1 and 365."
  }
}

variable "container_names" {
  description = "List of container names to create"
  type        = list(string)
  default     = []
}

variable "container_access_type" {
  description = "Access type for containers (private, blob, container)"
  type        = string
  default     = "private"
  validation {
    condition     = contains(["private", "blob", "container"], var.container_access_type)
    error_message = "Container access type must be private, blob, or container."
  }
}

variable "queue_names" {
  description = "List of queue names to create"
  type        = list(string)
  default     = []
}

variable "table_names" {
  description = "List of table names to create"
  type        = list(string)
  default     = []
}

variable "enable_network_rules" {
  description = "Enable network rules for the Storage Account"
  type        = bool
  default     = false
}

variable "default_network_action" {
  description = "Default action for network rules (Allow or Deny)"
  type        = string
  default     = "Deny"
  validation {
    condition     = contains(["Allow", "Deny"], var.default_network_action)
    error_message = "Default network action must be Allow or Deny."
  }
}

variable "network_bypass" {
  description = "List of services to bypass network rules"
  type        = list(string)
  default     = ["AzureServices"]
}

variable "ip_rules" {
  description = "List of IP addresses or CIDR blocks to allow"
  type        = list(string)
  default     = []
}

variable "virtual_network_subnet_ids" {
  description = "List of virtual network subnet IDs to allow"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to the Storage Account resources"
  type        = map(string)
  default     = {}
}

# Lifecycle Management Variables
variable "enable_lifecycle_management" {
  description = "Enable lifecycle management policies for raw events"
  type        = bool
  default     = true
}

variable "archive_after_days" {
  description = "Number of days after which to transition blobs to Archive tier"
  type        = number
  default     = 90
  validation {
    condition     = var.archive_after_days >= 1 && var.archive_after_days <= 2555
    error_message = "Archive after days must be between 1 and 2555 (7 years)."
  }
}

variable "delete_after_days" {
  description = "Number of days after which to delete blobs (must be greater than archive_after_days)"
  type        = number
  default     = 365
  validation {
    condition     = var.delete_after_days >= 1 && var.delete_after_days <= 2555
    error_message = "Delete after days must be between 1 and 2555 (7 years)."
  }
}

# CORS Configuration (optional)
variable "enable_cors" {
  description = "Enable CORS for blob storage"
  type        = bool
  default     = false
}

variable "cors_allowed_origins" {
  description = "List of allowed origins for CORS"
  type        = list(string)
  default     = []
}

variable "cors_allowed_methods" {
  description = "List of allowed HTTP methods for CORS"
  type        = list(string)
  default     = ["GET", "HEAD", "OPTIONS"]
}

variable "cors_allowed_headers" {
  description = "List of allowed headers for CORS"
  type        = list(string)
  default     = ["*"]
}

variable "cors_exposed_headers" {
  description = "List of exposed headers for CORS"
  type        = list(string)
  default     = ["*"]
}

variable "cors_max_age_in_seconds" {
  description = "Maximum age in seconds for CORS preflight requests"
  type        = number
  default     = 3600
}

