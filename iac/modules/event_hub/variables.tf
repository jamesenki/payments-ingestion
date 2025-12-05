variable "namespace_name" {
  description = "The name of the Event Hub Namespace"
  type        = string
}

variable "eventhub_name" {
  description = "The name of the Event Hub"
  type        = string
}

variable "location" {
  description = "The Azure region where the Event Hub will be created"
  type        = string
}

variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "sku" {
  description = "The SKU of the Event Hub Namespace (Basic, Standard, Premium)"
  type        = string
  default     = "Standard"
  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.sku)
    error_message = "SKU must be Basic, Standard, or Premium."
  }
}

variable "capacity" {
  description = "The capacity (throughput units) of the Event Hub Namespace"
  type        = number
  default     = 1
  validation {
    condition     = var.capacity >= 1 && var.capacity <= 20
    error_message = "Capacity must be between 1 and 20."
  }
}

variable "auto_inflate_enabled" {
  description = "Enable auto-inflate for the Event Hub Namespace"
  type        = bool
  default     = false
}

variable "maximum_throughput_units" {
  description = "Maximum throughput units when auto-inflate is enabled"
  type        = number
  default     = 20
}

variable "partition_count" {
  description = "The number of partitions for the Event Hub"
  type        = number
  default     = 2
  validation {
    condition     = var.partition_count >= 1 && var.partition_count <= 32
    error_message = "Partition count must be between 1 and 32."
  }
}

variable "message_retention" {
  description = "The number of days to retain messages in the Event Hub"
  type        = number
  default     = 1
  validation {
    condition     = var.message_retention >= 1 && var.message_retention <= 7
    error_message = "Message retention must be between 1 and 7 days."
  }
}

variable "consumer_groups" {
  description = "List of consumer group names to create"
  type        = list(string)
  default     = ["default"]
}

variable "tags" {
  description = "Tags to apply to the Event Hub resources"
  type        = map(string)
  default     = {}
}

