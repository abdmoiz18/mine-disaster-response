variable "name" {}
variable "resource_group_name" {}
variable "location" {}
variable "sku" {}
variable "iot_hub_name" {}
variable "iot_hub_namespace" {}
variable "cosmos_db_account_name" {}
variable "cosmos_db_database_name" {}
variable "cosmos_db_container_name" {}
variable "tags" {}

## Data source to get keys from existing resources
data "azurerm_iothub" "iothub" {
  name                = var.iot_hub_name
  resource_group_name = var.resource_group_name
}

# This explicitly looks up the 'iothubowner' policy to get its key
data "azurerm_iothub_shared_access_policy" "iothubowner_policy" {
  name                = "iothubowner"
  resource_group_name = var.resource_group_name
  iothub_name         = var.iot_hub_name
}

data "azurerm_cosmosdb_account" "cosmosdb" {
  name                = var.cosmos_db_account_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_stream_analytics_job" "job" {
  name                         = var.name
  resource_group_name          = var.resource_group_name
  location                     = var.location
  compatibility_level          = "1.2"
  data_locale                  = "en-US"
  streaming_units              = 1 # StandardV2 allows 1, 2, 4, 8...
  
  sku_name = var.sku

  transformation_query = file("${path.module}/query.sql")

  tags = var.tags
}

resource "azurerm_stream_analytics_stream_input_iothub" "iothub_input" {
  name                         = "iothub-input"
  stream_analytics_job_name    = azurerm_stream_analytics_job.job.name
  resource_group_name          = var.resource_group_name
  endpoint                     = "messages/events"
  # Ensure the "streamanalytics" consumer group exists in the IoT Hub.
  # If it does not exist, create it in the IoT Hub configuration.
  eventhub_consumer_group_name = "streamanalytics" # Matches consumer group in iot-hub module
  iothub_namespace             = var.iot_hub_namespace
  shared_access_policy_key     = data.azurerm_iothub_shared_access_policy.iothubowner_policy.primary_key
  shared_access_policy_name    = "iothubowner"

  serialization {
    type     = "Json"
    encoding = "UTF8"
  }
}

# Data source to get the Cosmos DB Database ID
data "azurerm_cosmosdb_sql_database" "db" {
  name                = var.cosmos_db_database_name
  resource_group_name = var.resource_group_name
  account_name        = var.cosmos_db_account_name
}

resource "azurerm_stream_analytics_output_cosmosdb" "cosmos_output" {
  name                      = "cosmosdb-output"
  stream_analytics_job_id   = azurerm_stream_analytics_job.job.id
  cosmosdb_account_key      = data.azurerm_cosmosdb_account.cosmosdb.primary_key
  cosmosdb_sql_database_id  = data.azurerm_cosmosdb_sql_database.db.id
  container_name            = var.cosmos_db_container_name
  document_id               = "id"
  partition_key             = "device_id"
}

output "job_id" {
  description = "The ID of the Stream Analytics job."
  value       = azurerm_stream_analytics_job.job.job_id
}
