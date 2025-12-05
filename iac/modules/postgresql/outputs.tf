output "server_id" {
  description = "The ID of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.this.id
}

output "server_name" {
  description = "The name of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.this.name
}

output "server_fqdn" {
  description = "The fully qualified domain name of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.this.fqdn
}

output "administrator_login" {
  description = "The administrator login for the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.this.administrator_login
  sensitive   = true
}

output "database_ids" {
  description = "Map of database names to their IDs"
  value = {
    for db_name, db in azurerm_postgresql_flexible_server_database.this : db_name => db.id
  }
}

output "database_names" {
  description = "List of database names created"
  value       = [for db in azurerm_postgresql_flexible_server_database.this : db.name]
}

output "connection_string" {
  description = "PostgreSQL connection string"
  value       = "postgresql://${var.administrator_login}@${azurerm_postgresql_flexible_server.this.name}:${var.administrator_password}@${azurerm_postgresql_flexible_server.this.fqdn}:5432"
  sensitive   = true
}

