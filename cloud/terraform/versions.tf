terraform {
    required_providers {
        azurerm = {
            source = "hashicorp/azurerm"
            version = "~> 3.0"
        }
    }

    # This is commented until there is a storage account for state
    # backend "azurerm" {
    #    resource_group_name = "terraform-state-rg"
    #    storage_account_name = "mineterraformstate"
    #    container_name = "tfstate"
    #    key = "mine-disaster.tfstate"
    #}
}

provider "azurerm" {
    features {}
}
