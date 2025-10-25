# Resource Group
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# IoT Hub
module "iot_hub" {
  source              = "./modules/iot-hub"
  name                = var.iot_hub_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  sku_name            = var.iot_hub_sku_name
  tags                = var.tags
}

# Cosmos DB Account
module "cosmos_db" {
  source              = "./modules/cosmos-db"
  name                = var.cosmos_db_account_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  tags                = var.tags
}

# Stream Analytics Job
module "stream_analytics" {
  source                    = "./modules/stream-analytics"
  name                      = var.stream_analytics_job_name
  resource_group_name       = azurerm_resource_group.rg.name
  location                  = var.location
  sku                       = var.stream_analytics_sku
  iot_hub_name              = var.iot_hub_name
  iot_hub_namespace         = module.iot_hub.iot_hub_namespace
  cosmos_db_account_name    = module.cosmos_db.account_name
  cosmos_db_database_name   = var.cosmos_db_database_name
  cosmos_db_container_name  = "miner_telemetry"
  tags                      = var.tags
}
