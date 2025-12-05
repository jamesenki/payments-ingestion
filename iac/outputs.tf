output "resource_group_name" {
  description = "The name of the resource group"
  value       = var.resource_group_name
}

output "location" {
  description = "The Azure region where resources are deployed"
  value       = var.location
}

output "environment" {
  description = "The deployment environment"
  value       = var.environment
}

output "common_tags" {
  description = "Common tags applied to all resources"
  value       = var.tags
}

