resource "azurerm_storage_account" "function_storage" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = var.storage_replication_type

  # Security settings
  min_tls_version           = "TLS1_2"
  enable_https_traffic_only = true

  tags = var.tags
}

resource "azurerm_service_plan" "this" {
  name                = var.app_service_plan_name
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  sku_name            = var.sku_name

  tags = var.tags
}

resource "azurerm_linux_function_app" "this" {
  name                       = var.function_app_name
  location                   = var.location
  resource_group_name        = var.resource_group_name
  service_plan_id            = azurerm_service_plan.this.id
  storage_account_name       = azurerm_storage_account.function_storage.name
  storage_account_access_key = azurerm_storage_account.function_storage.primary_access_key

  site_config {
    application_stack {
      python_version = var.python_version
    }

    # Enable Application Insights
    application_insights_key               = var.application_insights_key
    application_insights_connection_string = var.application_insights_connection_string

    # Security and performance settings
    ftps_state                  = "FtpsOnly"
    minimum_tls_version         = "1.2"
    http2_enabled               = true
    always_on                   = var.always_on
  }

  app_settings = merge(
    {
      "FUNCTIONS_WORKER_RUNTIME"       = "python"
      "ENABLE_ORYX_BUILD"              = "true"
      "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
      "WEBSITE_RUN_FROM_PACKAGE"       = "1"
    },
    var.app_settings
  )

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [
      app_settings["WEBSITE_RUN_FROM_PACKAGE"],
    ]
  }
}

