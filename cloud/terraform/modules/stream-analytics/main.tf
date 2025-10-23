variable "name" {}
variable "resource_group_name" {}
variable "location" {}
variable "sku" {}
variable "iot_hub_id" {}
variable "cosmos_db_account_name" {}
variable "cosmos_db_database_name" {}
variable "cosmos_db_container_name" {}
variable "tags" {}

resource "azurerm_stream_analytics_job" "job" {
    name = var.name
    resource_group_name = var.resource_group_name
    location = var.location
    compatibility_level = "1.2"
    data_locale = "en-US"
    events_late_arrival_max_delay_in_seconds = 60
    events_out_of_order_max_delay_in_seconds = 50
    events_out_of_order_policy = "Adjust"
    output_error_policy = "Stop"
    streaming_units = 3

    tags = var.tags

    transformation_query = file("${path.module}/query.sql")

    depends_on = [local_file.query_file]
}

# Store the query in a separate file for readability
resource "local_file" "query_file" {
    filename = "${path.module}/query.sql"
    content = <<-EOT
  -- Process Miner Telemetry
  WITH MinerTelemetry AS (
    SELECT
      miner.device_id,
      miner.device_timestamp,
      miner.ble_readings,
      miner.imu_data,
      miner.battery,
      miner.position.x AS location_x,
      miner.position.y AS location_y,
      'miner_telemetry' AS message_type,
      CONCAT(miner.device_id, '-', REPLACE(REPLACE(REPLACE(miner.device_timestamp, ':', ''), '.', ''), '-', '')) AS id
    FROM
      [iothub-input] as miner
    WHERE
      miner.message_type = 'miner_telemetry'
  ),
  
  -- Process gateway status
  GatewayStatus AS (
    SELECT
      gateway.gateway_id AS device_id,
      gateway.timestamp AS device_timestamp,
      gateway.miners_tracked,
      gateway.status,
      'gateway_status' AS message_type,
      CONCAT(gateway.gateway_id, '-', REPLACE(REPLACE(REPLACE(gateway.timestamp, ':', ''), '.', ''), '-', '')) AS id
    FROM
      [iothub-input] as gateway
    WHERE
      gateway.message_type = 'gateway_status'
  )
  
  -- Output miner telemetry
  SELECT * INTO [cosmos-output] FROM MinerTelemetry
  UNION ALL
  SELECT * INTO [cosmos-output] FROM GatewayStatus
  EOT
}

# Data sources to get existing resource details

# IoT Hub input
resource "azurerm_stream_analytics_stream_input_iothub" "iothub_input" {
    name = "iothub-input"
    stream_analytics_job_name = azurerm_stream_analytics_job.job.name
    resource_group_name = var.resource_group_name
    endpoint = "messages/events"
    eventhub_consumer_group_name = "streamanalytics"
    iothub_namespace = basename(var.iot_hub_id)
    shared_access_policy_key = data.azurerm_iothub_shared_access_policy.iothub_policy.primary_key
    shared_access_policy_name = "iothubowner"

    serialization {
        type = "Json"
        encoding = "UTF8"
    }
}
    account_key = data.azurerm_cosmosdb_account.cosmos_db.primary_key
# Cosmos DB Output
resource "azurerm_stream_analytics_output_cosmosdb" "cosmos_output" {
    name = "cosmos-output"
    stream_analytics_job_name = azurerm_stream_analytics_job.job.name
    resource_group_name = var.resource_group_name
    account_id = data.azurerm_cosmosdb_account.cosmos_db.id
    account_key = data.azurerm_cosmosdb_account.cosmos_db.primary_key
    database = var.cosmos_db_database_name
    container_name = var.cosmos_db_container_name
    document_id = "id"
}

# Data sources to get existing resource details
data "azurerm_iothub_shared_access_policy" "iothub_policy" {
  name                = "iothubowner"
  resource_group_name = var.resource_group_name
  iothub_name         = basename(var.iot_hub_id)
}

data "azurerm_cosmosdb_account" "cosmos_db" {
  name                = var.cosmos_db_account_name
  resource_group_name = var.resource_group_name
}