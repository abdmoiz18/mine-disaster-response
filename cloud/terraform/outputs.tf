# ===================================================================
# IoT Hub Outputs
# ===================================================================
output "iot_hub_service_connection_string" {
  description = "Primary service connection string for the IoT Hub. Use this for backend applications, not devices."
  # FIX: Ensure this matches the output name from the module
  value       = module.iot_hub.service_connection_string
  sensitive   = true
}

output "iot_hub_hostname" {
  description = "The hostname of the IoT Hub, used for device connection configuration."
  value       = module.iot_hub.hostname
}

# ===================================================================
# Cosmos DB Outputs
# ===================================================================
output "cosmosdb_primary_key" {
  description = "The primary key for the Cosmos DB account. Required for SDK connections."
  value       = module.cosmos_db.primary_key
  sensitive   = true
}

output "cosmosdb_endpoint" {
  description = "The endpoint URL of the Cosmos DB account."
  # FIX: Ensure this matches the output name from the module
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
