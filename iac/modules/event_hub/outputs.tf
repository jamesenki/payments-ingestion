output "namespace_id" {
  description = "The ID of the Event Hub Namespace"
  value       = azurerm_eventhub_namespace.this.id
}

output "namespace_name" {
  description = "The name of the Event Hub Namespace"
  value       = azurerm_eventhub_namespace.this.name
}

output "eventhub_id" {
  description = "The ID of the Event Hub"
  value       = azurerm_eventhub.this.id
}

output "eventhub_name" {
  description = "The name of the Event Hub"
  value       = azurerm_eventhub.this.name
}

output "primary_connection_string" {
  description = "The primary connection string for the Event Hub Namespace"
  value       = azurerm_eventhub_namespace.this.default_primary_connection_string
  sensitive   = true
}

output "secondary_connection_string" {
  description = "The secondary connection string for the Event Hub Namespace"
  value       = azurerm_eventhub_namespace.this.default_secondary_connection_string
  sensitive   = true
}

output "send_connection_string" {
  description = "The connection string with send permissions"
  value       = azurerm_eventhub_authorization_rule.send.primary_connection_string
  sensitive   = true
}

output "listen_connection_string" {
  description = "The connection string with listen permissions"
  value       = azurerm_eventhub_authorization_rule.listen.primary_connection_string
  sensitive   = true
}

output "consumer_groups" {
  description = "Map of consumer group names to their IDs"
  value = {
    for cg_name, cg in azurerm_eventhub_consumer_group.this : cg_name => cg.id
  }
}

