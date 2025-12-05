variable "function_app_name" {
  description = "The name of the Function App"
  type        = string
}

variable "app_service_plan_name" {
  description = "The name of the App Service Plan"
  type        = string
}

variable "storage_account_name" {
  description = "The name of the Storage Account for the Function App"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "Storage account name must be 3-24 characters, lowercase letters and numbers only."
  }
}

variable "location" {
  description = "The Azure region where the Function App will be created"
  type        = string
}

variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "sku_name" {
  description = "The SKU for the App Service Plan (e.g., Y1 for Consumption, EP1 for Premium, S1 for Standard)"
  type        = string
  default     = "Y1"
}

variable "python_version" {
  description = "The Python version for the Function App"
  type        = string
  default     = "3.11"
  validation {
    condition     = contains(["3.8", "3.9", "3.10", "3.11"], var.python_version)
    error_message = "Python version must be 3.8, 3.9, 3.10, or 3.11."
  }
}

variable "always_on" {
  description = "Should the Function App be always on (not applicable for Consumption plan)"
  type        = bool
  default     = false
}

variable "app_settings" {
  description = "Additional application settings for the Function App"
  type        = map(string)
  default     = {}
}

variable "application_insights_key" {
  description = "The Application Insights instrumentation key"
  type        = string
  default     = null
}

variable "application_insights_connection_string" {
  description = "The Application Insights connection string"
  type        = string
  default     = null
}

variable "storage_replication_type" {
  description = "The replication type for the Function App's storage account (LRS, GRS, RAGRS, ZRS, GZRS, RAGZRS)"
  type        = string
  default     = "LRS"
  validation {
    condition     = contains(["LRS", "GRS", "RAGRS", "ZRS", "GZRS", "RAGZRS"], var.storage_replication_type)
    error_message = "Replication type must be LRS, GRS, RAGRS, ZRS, GZRS, or RAGZRS."
  }
}

variable "tags" {
  description = "Tags to apply to the Function App resources"
  type        = map(string)
  default     = {}
}

