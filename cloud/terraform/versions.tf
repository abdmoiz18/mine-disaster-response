terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      # This allows for non-breaking updates
      version = "~> 3.0"
    }
  }
  # ==> BEST PRACTICE: Configure Remote State <==
  # See: https://developer.hashicorp.com/terraform/tutorials/azure/azure-storage-account for official guidance.
  # ==> BEST PRACTICE: Configure Remote State <==
  # This block should be uncommented after you create a dedicated storage account.
  # It prevents losing your state file and allows for team collaboration.
  #
  # backend "azurerm" {
  #   storage_account_name = "protominerespterraform" # Must be globally unique (Azure Storage Account names must be globally unique and follow Azure naming conventions)
  #   storage_account_name = "protominerespterraform" # Must be globally unique
  #   container_name       = "tfstate"
  #   key                  = "prod.terraform.tfstate"
  # }
}

# Configure the Azure Provider
# The 'features {}' block is required for the azurerm provider and enables provider-specific features.
provider "azurerm" {
  features {}
}
