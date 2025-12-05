terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
    
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Resource Group
resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location

  tags = local.common_tags
}

# Local variables for naming and tagging
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  region_short = {
    "East US"   = "eus"
    "West US"   = "wus"
    "East US 2" = "eus2"
  }

  location_short = lookup(local.region_short, var.location, "eus")

  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

# Event Hub Module
module "event_hub" {
  source = "../../modules/event_hub"

  namespace_name      = "${local.name_prefix}-evhns-${local.location_short}"
  eventhub_name       = "${local.name_prefix}-evh-${local.location_short}"
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name

  sku                      = var.eventhub_sku
  capacity                 = var.eventhub_capacity
  partition_count          = var.eventhub_partition_count
  message_retention        = var.eventhub_message_retention
  auto_inflate_enabled     = var.eventhub_auto_inflate_enabled
  maximum_throughput_units = var.eventhub_maximum_throughput_units

  consumer_groups = var.eventhub_consumer_groups

  tags = local.common_tags
}

# Storage Account Module (for general use)
module "storage_account" {
  source = "../../modules/storage_account"

  storage_account_name = replace("${var.project_name}${var.environment}st${local.location_short}", "-", "")
  location             = var.location
  resource_group_name  = azurerm_resource_group.this.name

  account_tier       = var.storage_account_tier
  replication_type   = var.storage_replication_type
  account_kind       = "StorageV2"
  allow_public_access = false

  container_names = var.storage_container_names
  queue_names     = var.storage_queue_names
  table_names     = var.storage_table_names

  enable_versioning                = true
  delete_retention_days            = 7
  container_delete_retention_days  = 7

  tags = local.common_tags
}

# Function App Module
module "function_app" {
  source = "../../modules/function_app"

  function_app_name        = "${local.name_prefix}-func-${local.location_short}"
  app_service_plan_name    = "${local.name_prefix}-asp-${local.location_short}"
  storage_account_name     = replace("${var.project_name}${var.environment}funcst${local.location_short}", "-", "")
  storage_replication_type = "LRS"
  location                 = var.location
  resource_group_name      = azurerm_resource_group.this.name

  sku_name       = var.function_app_sku
  python_version = var.function_app_python_version
  always_on      = var.function_app_always_on

  app_settings = merge(
    var.function_app_settings,
    {
      "EVENTHUB_CONNECTION_STRING" = module.event_hub.listen_connection_string
      "STORAGE_CONNECTION_STRING"  = module.storage_account.primary_connection_string
    }
  )

  tags = local.common_tags
}

# PostgreSQL Module
module "postgresql" {
  source = "../../modules/postgresql"

  server_name         = "${local.name_prefix}-psql-${local.location_short}"
  location            = var.location
  resource_group_name = azurerm_resource_group.this.name

  postgresql_version     = var.postgresql_version
  administrator_login    = var.postgresql_admin_login
  administrator_password = var.postgresql_admin_password

  sku_name   = var.postgresql_sku
  storage_mb = var.postgresql_storage_mb

  backup_retention_days        = var.postgresql_backup_retention_days
  geo_redundant_backup_enabled = var.postgresql_geo_redundant_backup
  high_availability_mode       = var.postgresql_high_availability_mode

  database_names = var.postgresql_database_names

  allow_azure_services = true
  firewall_rules       = var.postgresql_firewall_rules

  tags = local.common_tags
}

