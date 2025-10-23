resource "azurerm_resource_group" "rg" {
    name = var.resource_group_name
    location = var.location
    # Tags to organize resources.
    tags = var.tags
}

# IoT Hub
module "iot_hub" {
    source = "./modules/iot-hub"
    name = "${var.project_name}-iothub"
    resource_group_name = azurerm_resource_group.rg.name
    location = var.location
    # Specifies the SKU (pricing tier) for the IoT Hub.
    sku = var.iot_hub_sku
    # Tags to organize resources.
    tags = var.tags
}

# Cosmos DB
module "cosmos_db" {
    source = "./modules/cosmos-db"
    name = "${var.project_name}-cosmosdb"
    resource_group_name = azurerm_resource_group.rg.name
    location = var.location
    # Specifies the RU/s (Request Units per second) provisioned throughput for the Cosmos DB account.
    throughput = var.cosmos_db_throughput
    tags = var.tags
}

# Stream Analytics
module "stream_analytics" {
    source = "./modules/stream-analytics"
    name = "${var.project_name}-streamanalytics"
    resource_group_name = azurerm_resource_group.rg.name
    location = var.location
    # Specifies the SKU (pricing tier) for the Stream Analytics job.
    sku = var.stream_analytics_sku
    iot_hub_id = module.iot_hub.iot_hub_id
    cosmos_db_account_name = module.cosmos_db.account_name
    cosmos_db_database_name = module.cosmos_db.database_name
    cosmos_db_container_name = module.cosmos_db.container_name
    # Tags to organize resources.
    tags = var.tags
}
