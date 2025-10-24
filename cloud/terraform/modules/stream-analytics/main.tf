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
  # ==> FIX: Use the new variable directly <==
  name                = var.iot_hub_name
  resource_group_name = var.resource_group_name
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
  shared_access_policy_key     = lookup({for p in data.azurerm_iothub.iothub.shared_access_policy : p.name => p.primary_key}, "service", "")
  shared_access_policy_name    = "service"

  serialization {
    type     = "Json"
    encoding = "UTF8"
  }
}

resource "azurerm_stream_analytics_output_cosmosdb" "cosmos_output" {
  name                      = "cosmosdb-output"
  stream_analytics_job_name = azurerm_stream_analytics_job.job.name
  resource_group_name       = var.resource_group_name
  account_name              = data.azurerm_cosmosdb_account.cosmosdb.name
  account_key               = data.azurerm_cosmosdb_account.cosmosdb.primary_key
  database                  = var.cosmos_db_database_name
  container_name            = var.cosmos_db_container_name
  document_id               = "id"
  # The partition_key "device_id" must match the partition key defined in the Cosmos DB container schema.
  partition_key             = "device_id"
}

# Ensure the query file exists
resource "local_file" "query_file" {
  filename = "${path.module}/query.sql"
  content  = file("${path.module}/query.sql")
}

output "job_id" {
  description = "The ID of the Stream Analytics job."
  value       = azurerm_stream_analytics_job.job.job_id
}
