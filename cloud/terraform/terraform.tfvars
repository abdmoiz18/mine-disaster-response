project_name = "mine-response"
location = "centralindia"
resource_group_name = "mine_disaster_rg"
iot_hub_sku = "S1"
cosmos_db_throughput = 400
stream_analytics_sku = "Standard"

tags = {
  Environment = "development"
  Project     = "Mine Disaster Response"
  Owner       = "abdmoiz18"
  ManagedBy   = "Terraform"
}