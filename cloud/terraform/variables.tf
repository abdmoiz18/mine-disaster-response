variable "project_name" {
  description = "Base name used for constructing resource names"
  default     = "proto-mine-resp"
}

variable "location" {
  description = "Azure region for all resources"
  default     = "centralindia"
}

variable "resource_group_name" {
  description = "Resource group for all resources"
  default     = "azure-iot-rg"
}

variable "tags" {
  description = "Tags to apply to all resources (example: { Environment = \"Dev\", Group = \"Capstone\", Project = \"MineResp\", Semester = \"7\", ManagedBy = \"Terraform\" })"
  type        = map(string)
  default = {
    Environment = "Dev"
    Group       = "Capstone"
    Project     = "MineResp"
    Semester    = "7"
    ManagedBy   = "Terraform"
  }
}

# Resource-specific names to ensure compatibility with existing Azure infrastructure
variable "iot_hub_name" {
  description = "Name of the existing IoT Hub"
  default     = "proto-mine-resp"
}

variable "cosmos_db_account_name" {
  description = "Name of the existing Cosmos DB Account"
  default     = "proto-mine-resp-cosmosdb"
}

variable "stream_analytics_job_name" {
  description = "Name of the existing Stream Analytics Job"
  default     = "mine-data-pipeline"
}

variable "cosmos_db_database_name" {
  description = "The name of the Cosmos DB SQL database."
  type        = string
  default     = "miner_navigation"
}

# SKU variables for IoT Hub and Stream Analytics resources
variable "iot_hub_sku_name" {
  description = "SKU Name for IoT Hub (F1 for Free)"
  default     = "F1"
}

variable "iot_hub_sku_tier" {
  description = "SKU Tier for IoT Hub"
  default     = "Free"
}

variable "stream_analytics_sku" {
  description = "SKU for Stream Analytics"
  default     = "StandardV2"
}
