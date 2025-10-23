variable "name" {}
variable "resource_group_name" {}
variable "location" {}
variable "sku" {}
variable "tags" {}

resource "azurerm_iothub" "iothub" {
    name = var.name
    resource_group_name = var.resource_group_name
    location = var.location

    sku {
        name = var.sku
        capacity = 1
    }

    tags = var.tags

    shared_access_policy {
        name = "iothubowner"
        rights = [
            "RegistryRead",
            "RegistryWrite",
            "ServiceConnect",
            "DeviceConnect"
        ]
    }
}

# Create a consumer group for Stream Analytics
resource "azurerm_iothub_consumer_group" "stream_analytics" {
    name = "streamanalytics"
    iothub_name = azurerm_iothub.iothub.name
    resource_group_name = var.resource_group_name
    eventhub_endpoint_name = "events"
}

output "id" {
    value = azurerm_iothub.iothub.id
}

output "hostname" {
    value = azurerm_iothub.iothub.hostname
}

output "connection_string" {
    value = azurerm_iothub.iothub.shared_access_policy[0].primary_connection_string
    sensitive = true
}
