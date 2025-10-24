# ===================================================================
# IoT Hub Outputs
# These are needed for your Raspberry Pi gateway and backend services.
# ===================================================================
output "iot_hub_service_connection_string" {
  description = "Primary service connection string for the IoT Hub. Use this for backend applications, not devices."
  value       = module.iot_hub.service_connection_string
  sensitive   = true # This prevents the value from being shown in `terraform apply` logs.
}

output "iot_hub_hostname" {
  description = "The hostname of the IoT Hub, used for device connection configuration."
  value       = module.iot_hub.hostname
}

# ===================================================================
# Cosmos DB Outputs
# These will be used by your Streamlit dashboard and any ML/analysis scripts.
# ===================================================================
output "cosmosdb_primary_key" {
  description = "The primary key for the Cosmos DB account. Required for SDK connections."
  value       = module.cosmos_db.primary_key
  sensitive   = true
}

output "cosmosdb_endpoint" {
  description = "The endpoint URL of the Cosmos DB account."
  value       = module.cosmos_db.endpoint
}

# ===================================================================
# General Infrastructure Outputs
# Useful for reference and scripting.
# ===================================================================
output "resource_group_name" {
  description = "The name of the resource group where all resources are deployed."
  value       = azurerm_resource_group.rg.name
}

output "stream_analytics_job_id" {
  description = "The ID of the Stream Analytics job."
  value       = module.stream_analytics.job_id
}
