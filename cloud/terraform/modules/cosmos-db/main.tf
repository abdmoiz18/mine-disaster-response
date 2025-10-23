variable "name" {}
variable "resource_group_name" {}
variable "location" {}
variable "throughput" {}
variable "tags" {}

resource "azurerm_cosmosdb_account" "db" {
    name = var.name
    location = var.location
    resource_group_name = var.resource_group_name
    offer_type = "Standard"
    kind = "GlobalDocumentDB"

    consistency_policy {
        consistency_level = "Session"
        max_interval_in_seconds = 5
        max_staleness_prefix = 100
    }

    geo_location {
        location = var.location
        failover_priority = 0
    }

    tags = var.tags
}

resource "azurerm_cosmosdb_sql_database" "miner_navigation" {
    name = "miner_navigation"
    resource_group_name = var.resource_group_name
    account_name = azurerm_cosmosdb_account.db.name
    throughput = var.throughput
}

resource "azurerm_cosmosdb_sql_container" "miner_telemetry" {
    name = "miner_telemetry"
    resource_group_name = var.resource_group_name
    account_name = azurerm_cosmosdb_account.db.name
    database_name = azurerm_cosmosdb_sql_database.miner_navigation.name
    partition_key_path = "/device_id"

    indexing_policy {
        indexing_mode = "consistent"

        included_path = {
            path = "/*"
        }

        # Exclude the "_etag" system property from indexing to optimize performance.
        excluded_path {
            path = "/\"_etag\"/?"
        }
    }
}

output "account_name" {
    value = azurerm_cosmosdb_account.db.name
}
# Assumes that azurerm_cosmosdb_account.db.connection_strings is non-empty.
# If the array may be empty, consider adding a validation or conditional logic.
output "connection_string" {
    value = azurerm_cosmosdb_account.db.connection_strings[0]
    sensitive = true
}
