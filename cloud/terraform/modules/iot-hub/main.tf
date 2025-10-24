variable "name" {}
variable "resource_group_name" {}
variable "location" {}
variable "sku_name" {}
variable "sku_tier" {}
variable "tags" {}

# This is the main resource block that defines the IoT Hub
resource "azurerm_iothub" "iothub" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location

  sku {
    name     = var.sku_name
    tier     = var.sku_tier
    capacity = 1
  }

  tags = var.tags
}

# This resource defines the consumer group for Stream Analytics
resource "azurerm_iothub_consumer_group" "stream_analytics" {
  name                   = "streamanalytics"
  iothub_name            = azurerm_iothub.iothub.name
  resource_group_name    = var.resource_group_name
  eventhub_endpoint_name = "events"
}

# This data source explicitly looks up the shared access policy by name.
# We are using the 'service' policy, which is best practice for backend apps.
data "azurerm_iothub_shared_access_policy" "service_policy" {
  name                = "service"
  resource_group_name = var.resource_group_name
  iothub_name         = azurerm_iothub.iothub.name
}

# --- MODULE OUTPUTS ---

output "iot_hub_namespace" {
  description = "The event hub-compatible namespace of the IoT Hub"
  value       = azurerm_iothub.iothub.event_hub_events_namespace
}

output "id" {
  value = azurerm_iothub.iothub.id
}

output "hostname" {
  value = azurerm_iothub.iothub.hostname
}

# This output now correctly references the data source we just added.
output "service_connection_string" {
  description = "The primary service connection string for the IoT Hub."
  value       = data.azurerm_iothub_shared_access_policy.service_policy.primary_connection_string
  sensitive   = true
}
