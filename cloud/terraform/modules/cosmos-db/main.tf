variable "name" {}
variable "resource_group_name" {}
variable "location" {}
variable "tags" {}

resource "azurerm_cosmosdb_account" "db" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  capabilities {
    name = "EnableServerless"
  }

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = var.location
    failover_priority = 0
  }

  tags = var.tags
}

resource "azurerm_cosmosdb_sql_database" "miner_navigation" {
  name                = "miner_navigation"
  resource_group_name = var.resource_group_name
  account_name        = azurerm_cosmosdb_account.db.name
  # Throughput is not set in Serverless mode
}

resource "azurerm_cosmosdb_sql_container" "miner_telemetry" {
  name                  = "miner_telemetry"
  resource_group_name   = var.resource_group_name
  account_name          = azurerm_cosmosdb_account.db.name
  database_name         = azurerm_cosmosdb_sql_database.miner_navigation.name
  partition_key_path    = "/device_id"
  # Throughput is not set in Serverless mode
}

output "account_name" {
  value = azurerm_cosmosdb_account.db.name
}

output "id" {
  value = azurerm_cosmosdb_account.db.id
}

output "primary_key" {
  value     = azurerm_cosmosdb_account.db.primary_key
  sensitive = true
}
