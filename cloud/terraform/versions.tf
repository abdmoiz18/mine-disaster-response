# Configuration of provider and backend

terraform {
    required_providers {
        azurerm = {
            source = "hashicorp/azurerm"
            version = "~> 3.0.0"
        }
    }

    # The backend configuration below is commented out.
    # To enable remote state storage, first create the Azure storage account and container.
    # Then, uncomment the backend block and update the resource_group_name, storage_account_name, container_name, and key as needed.
    # This will allow Terraform to store state remotely and enable collaboration.
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
