output "storage_account_id" {
  description = "The ID of the Storage Account"
  value       = azurerm_storage_account.this.id
}

output "storage_account_name" {
  description = "The name of the Storage Account"
  value       = azurerm_storage_account.this.name
}

output "primary_blob_endpoint" {
  description = "The primary blob endpoint"
  value       = azurerm_storage_account.this.primary_blob_endpoint
}

output "primary_queue_endpoint" {
  description = "The primary queue endpoint"
  value       = azurerm_storage_account.this.primary_queue_endpoint
}

output "primary_table_endpoint" {
  description = "The primary table endpoint"
  value       = azurerm_storage_account.this.primary_table_endpoint
}

output "primary_access_key" {
  description = "The primary access key for the Storage Account"
  value       = azurerm_storage_account.this.primary_access_key
  sensitive   = true
}

output "secondary_access_key" {
  description = "The secondary access key for the Storage Account"
  value       = azurerm_storage_account.this.secondary_access_key
  sensitive   = true
}

output "primary_connection_string" {
  description = "The primary connection string for the Storage Account"
  value       = azurerm_storage_account.this.primary_connection_string
  sensitive   = true
}

output "secondary_connection_string" {
  description = "The secondary connection string for the Storage Account"
  value       = azurerm_storage_account.this.secondary_connection_string
  sensitive   = true
}

output "identity_principal_id" {
  description = "The Principal ID of the Storage Account's managed identity"
  value       = azurerm_storage_account.this.identity[0].principal_id
}

output "container_ids" {
  description = "Map of container names to their resource IDs"
  value = {
    for container_name, container in azurerm_storage_container.this : container_name => container.id
  }
}

output "queue_ids" {
  description = "Map of queue names to their resource IDs"
  value = {
    for queue_name, queue in azurerm_storage_queue.this : queue_name => queue.id
  }
}

output "table_ids" {
  description = "Map of table names to their resource IDs"
  value = {
    for table_name, table in azurerm_storage_table.this : table_name => table.id
  }
}

output "lifecycle_management_policy_id" {
  description = "The ID of the lifecycle management policy for raw events (if enabled)"
  value       = var.enable_lifecycle_management ? azurerm_storage_management_policy.raw_events_lifecycle[0].id : null
}

