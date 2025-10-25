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
variable "job_storage_account_name" {
  description = "The name of the Storage Account for the Stream Analytics job."
  type        = string
}

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

data "azurerm_storage_account" "job_storage" {
  name                = var.job_storage_account_name
  resource_group_name = var.resource_group_name
}

resource "azurerm_stream_analytics_job" "job" {
  name                         = var.name
  resource_group_name          = var.resource_group_name
  location                     = var.location
  compatibility_level          = "1.2"
  data_locale                  = "en-US"
  streaming_units              = 10 # StandardV2 allows 1, 2, 4, 8...
  
  sku_name = var.sku

  transformation_query = file("${path.module}/query.sql")

  tags = var.tags

  content_storage_policy     = "JobStorageAccount"

  job_storage_account {
    account_name = data.azurerm_storage_account.job_storage.name
    account_key  = data.azurerm_storage_account.job_storage.primary_access_key
  }

  identity {
    type = "SystemAssigned"
  }

  lifecycle {
    ignore_changes = [
      transformation_query,
    ]
  }
}

resource "azurerm_stream_analytics_stream_input_iothub" "iothub_input" {
  name                         = "proto-mine-resp"
  stream_analytics_job_name    = azurerm_stream_analytics_job.job.name
  resource_group_name          = var.resource_group_name
  endpoint                     = "messages/events"
  eventhub_consumer_group_name = "$Default" # Match the live resource
  iothub_namespace             = "proto-mine-resp" # Match the live resource
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
  name                      = "miner-telemetry"
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
