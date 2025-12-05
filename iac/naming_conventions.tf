locals {
  # Naming convention: {project}-{environment}-{resource}-{region}
  name_prefix = "${var.project_name}-${var.environment}"
  
  # Short region code for naming (Azure has length limits for some resources)
  region_short = {
    "East US"        = "eus"
    "East US 2"      = "eus2"
    "West US"        = "wus"
    "West US 2"      = "wus2"
    "Central US"     = "cus"
    "North Central US" = "ncus"
    "South Central US" = "scus"
    "West Central US"  = "wcus"
    "North Europe"   = "neu"
    "West Europe"    = "weu"
  }

  location_short = lookup(local.region_short, var.location, "eus")

  # Standard resource names
  naming = {
    event_hub_namespace = "${local.name_prefix}-evhns-${local.location_short}"
    event_hub           = "${local.name_prefix}-evh-${local.location_short}"
    function_app        = "${local.name_prefix}-func-${local.location_short}"
    app_service_plan    = "${local.name_prefix}-asp-${local.location_short}"
    postgresql_server   = "${local.name_prefix}-psql-${local.location_short}"
    postgresql_database = "payments_db"
    storage_account     = replace("${var.project_name}${var.environment}st${local.location_short}", "-", "")
  }

  # Common tags to be applied to all resources
  common_tags = merge(
    var.tags,
    {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
      CreatedDate = timestamp()
    }
  )
}

output "resource_naming" {
  description = "Computed resource names following naming conventions"
  value       = local.naming
}

output "applied_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}

