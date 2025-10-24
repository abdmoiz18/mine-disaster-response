variable "name" {}
variable "resource_group_name" {}
variable "location" {}
variable "sku_name" {}
variable "sku_tier" {}
variable "tags" {}

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

# Always create a consumer group for Stream Analytics (Terraform will manage existence)
resource "azurerm_iothub_consumer_group" "stream_analytics" {
  name                   = "streamanalytics"
  iothub_name            = azurerm_iothub.iothub.name
  resource_group_name    = var.resource_group_name
  eventhub_endpoint_name = "events"
}

output "namespace" {
  value = azurerm_iothub.iothub.event_hub_events_namespace
}

output "id" {
  value = azurerm_iothub.iothub.id
}

output "hostname" {
  value = azurerm_iothub.iothub.hostname
}
