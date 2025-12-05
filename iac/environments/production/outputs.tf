output "resource_group_name" {
  description = "The name of the resource group"
  value       = azurerm_resource_group.this.name
}

output "resource_group_location" {
  description = "The location of the resource group"
  value       = azurerm_resource_group.this.location
}

# Event Hub Outputs
output "eventhub_namespace_name" {
  description = "The name of the Event Hub Namespace"
  value       = module.event_hub.namespace_name
}

output "eventhub_name" {
  description = "The name of the Event Hub"
  value       = module.event_hub.eventhub_name
}

output "eventhub_connection_string" {
  description = "The Event Hub connection string"
  value       = module.event_hub.primary_connection_string
  sensitive   = true
}

# Storage Account Outputs
output "storage_account_name" {
  description = "The name of the Storage Account"
  value       = module.storage_account.storage_account_name
}

output "storage_primary_connection_string" {
  description = "The primary connection string for the Storage Account"
  value       = module.storage_account.primary_connection_string
  sensitive   = true
}

output "storage_containers" {
  description = "The created storage containers"
  value       = module.storage_account.container_ids
}

# Function App Outputs
output "function_app_name" {
  description = "The name of the Function App"
  value       = module.function_app.function_app_name
}

output "function_app_default_hostname" {
  description = "The default hostname of the Function App"
  value       = module.function_app.function_app_default_hostname
}

output "function_app_identity_principal_id" {
  description = "The Principal ID of the Function App's managed identity"
  value       = module.function_app.function_app_identity_principal_id
}

# PostgreSQL Outputs
output "postgresql_server_name" {
  description = "The name of the PostgreSQL server"
  value       = module.postgresql.server_name
}

output "postgresql_server_fqdn" {
  description = "The FQDN of the PostgreSQL server"
  value       = module.postgresql.server_fqdn
}

output "postgresql_databases" {
  description = "The list of PostgreSQL databases"
  value       = module.postgresql.database_names
}

output "postgresql_connection_string" {
  description = "The PostgreSQL connection string"
  value       = module.postgresql.connection_string
  sensitive   = true
}

