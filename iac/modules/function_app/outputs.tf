output "function_app_id" {
  description = "The ID of the Function App"
  value       = azurerm_linux_function_app.this.id
}

output "function_app_name" {
  description = "The name of the Function App"
  value       = azurerm_linux_function_app.this.name
}

output "function_app_default_hostname" {
  description = "The default hostname of the Function App"
  value       = azurerm_linux_function_app.this.default_hostname
}

output "function_app_identity_principal_id" {
  description = "The Principal ID of the Function App's managed identity"
  value       = azurerm_linux_function_app.this.identity[0].principal_id
}

output "function_app_identity_tenant_id" {
  description = "The Tenant ID of the Function App's managed identity"
  value       = azurerm_linux_function_app.this.identity[0].tenant_id
}

output "app_service_plan_id" {
  description = "The ID of the App Service Plan"
  value       = azurerm_service_plan.this.id
}

output "storage_account_id" {
  description = "The ID of the Function App's storage account"
  value       = azurerm_storage_account.function_storage.id
}

output "storage_account_name" {
  description = "The name of the Function App's storage account"
  value       = azurerm_storage_account.function_storage.name
}

output "storage_account_primary_connection_string" {
  description = "The primary connection string for the Function App's storage account"
  value       = azurerm_storage_account.function_storage.primary_connection_string
  sensitive   = true
}

