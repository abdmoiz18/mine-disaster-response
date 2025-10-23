variable "project_name" {
    description = "Base name used for all resources"
    default = "mine-disaster"
}

variable "location" {
    description = "Azure region for all resources"
    default = "eastus"
}

variable "resource_group_name" {
    description = "Resource group for all resources"
    default = "mine-disaster-rg"
}

variable "tags" {
    description = "Tags to apply to all resources"
    type = map(string)
    default = {
        Environment = "dev"
        Project = "Mine Disaster Response"
        ManagedBy = "Terraform"
    }
}

# IoT Hub variables 
variable "iot_hub_sku" {
    description = "SKU for IoT Hub"
    default = "S1"
}

# Cosmos DB variables
variable "cosmos_db_throughput" {
    description = "RU/s for CosmosDB"
    default = 400
}

# Stream Analytics variables 
variable "stream_analytics_sku" {
    description = "SKU for Stream Analytics"
    default = "Standard"
}
