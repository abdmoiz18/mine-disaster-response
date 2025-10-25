# General Configuration - Matches your existing setup
location            = "Central India"
resource_group_name = "azure-iot-rg"

# Resource Specific Names - To match your existing infrastructure
iot_hub_name              = "proto-mine-resp"
cosmos_db_account_name    = "proto-mine-resp-cosmosdb"
stream_analytics_job_name = "mine-data-pipeline"

# SKU Configuration - To match your existing infrastructure
iot_hub_sku_name = "F1"
stream_analytics_sku = "StandardV2"

# Tags - Merging your existing tags with best practices
tags = {
  Environment = "Dev"
  Group       = "Capstone"
  Project     = "MineResp"
  Semester    = "7"
  Owner       = "abdmoiz18" # Azure AD login of the owner
  ManagedBy   = "Terraform"    # Best practice tag
}
