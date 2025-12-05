resource "azurerm_storage_account" "this" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = var.account_tier
  account_replication_type = var.replication_type
  account_kind             = var.account_kind

  # Security settings
  min_tls_version                 = "TLS1_2"
  enable_https_traffic_only       = true
  allow_nested_items_to_be_public = var.allow_public_access

  # Advanced threat protection
  blob_properties {
    versioning_enabled  = var.enable_versioning
    change_feed_enabled = var.enable_change_feed

    delete_retention_policy {
      days = var.delete_retention_days
    }

    container_delete_retention_policy {
      days = var.container_delete_retention_days
    }
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

resource "azurerm_storage_container" "this" {
  for_each = toset(var.container_names)

  name                  = each.value
  storage_account_name  = azurerm_storage_account.this.name
  container_access_type = var.container_access_type
}

resource "azurerm_storage_queue" "this" {
  for_each = toset(var.queue_names)

  name                 = each.value
  storage_account_name = azurerm_storage_account.this.name
}

resource "azurerm_storage_table" "this" {
  for_each = toset(var.table_names)

  name                 = each.value
  storage_account_name = azurerm_storage_account.this.name
}

# Optional: Storage Account Network Rules
resource "azurerm_storage_account_network_rules" "this" {
  count = var.enable_network_rules ? 1 : 0

  storage_account_id = azurerm_storage_account.this.id

  default_action             = var.default_network_action
  bypass                     = var.network_bypass
  ip_rules                   = var.ip_rules
  virtual_network_subnet_ids = var.virtual_network_subnet_ids
}

