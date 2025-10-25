# Azure Functions - Next Steps & Development Guide

**Last Updated:** 2025-10-25
**Author:** abdmoiz18

This document outlines the plan for developing and deploying the Azure Functions required for this project. It's intended to be a guide for when we pick this work back up.

## 1. Current Status

*   This `functions/` directory is currently a placeholder for our Python application code.
*   The infrastructure for the Azure Function App (the app itself, the hosting plan, storage, etc.) has **not** yet been defined in Terraform.
*   The core infrastructure (IoT Hub, Stream Analytics, Cosmos DB, and a Resource Group) has been defined and is managed by Terraform.

## 2. Objective

The primary goal of our first Azure Function will be to **react to new data arriving in our Cosmos DB container**.

The data flow is: `IoT Device -> IoT Hub -> Stream Analytics -> Cosmos DB`. The function will act as the next step in the pipeline, triggered by the `CosmosDBTrigger`. Its job will be to take the new document from the database and perform some kind of processing, such as:
*   Running a machine learning model inference.
*   Performing further data transformation.
*   Calling an external API.

## 3. Action Plan: From Zero to a Deployed Function

Follow these steps in order to build and deploy the function securely and maintainably.

### Step 1: Provision the Infrastructure with Terraform

Before writing any Python code, we must first define the Azure resources the function will run on.

1.  **Create a new Terraform Module:** Create a new folder named `modules/functions`.
2.  **Define the Resources:** Inside the new module, create a `main.tf` and `variables.tf`. Define the following resources:
    *   An **App Service Plan** (`azurerm_service_plan`) to host the function.
    *   A dedicated **Storage Account** (`azurerm_storage_account`) for the function's operational needs.
    *   The **Function App** (`azurerm_function_app`) itself.
3.  **Crucially, Enable Managed Identity:** In the `azurerm_function_app` resource block, enable a system-assigned managed identity. This is the key to secure, credential-less authentication.
    ```hcl
    # In your new modules/functions/main.tf
    resource "azurerm_function_app" "this" {
      # ... other required arguments
      identity {
        type = "SystemAssigned"
      }
    }
    ```

### Step 2: Implement Secure Secret Management (The "Why")

Our function needs the connection string for the Cosmos DB trigger. We **must not** hard-code this or place it in plaintext configuration. The professional standard is to use Azure Key Vault.

1.  **Add a Key Vault Module:** If not already done, create a Terraform module for `azurerm_key_vault`.
2.  **Store Outputs as Secrets:** In the root `main.tf`, add `azurerm_key_vault_secret` resources to automatically store the primary key and connection string from the `cosmos_db` module output into the Key Vault.
3.  **Grant Access to the Function:** Add an `azurerm_key_vault_access_policy` resource. This policy will grant the Function App's Managed Identity (from Step 1) `get` and `list` permissions on secrets in the Key Vault.

**Why this way?**
*   **Security:** Secrets are never exposed in code or config files. They are fetched dynamically at runtime.
*   **Maintainability:** If you need to rotate the Cosmos DB keys, you simply re-run `terraform apply`. The secrets in Key Vault are updated, and the Function App picks up the new key on its next startup. No application code changes or redeployment are needed.

### Step 3: Develop the Python Function Code

Now you can write the code inside this `functions/` directory.

1.  **Initialize the project:** Use the Azure Functions Core Tools: `func init --python`.
2.  **Create the function:** Create a new function with a Cosmos DB Trigger: `func new --name CosmosTrigger --template "Cosmos DB trigger"`.
3.  **Configure the Trigger (`function.json`):** The `connectionStringSetting` in your `function.json` should **NOT** contain the actual connection string. It should contain the name of the App Setting that will hold the string.
    ```json
    {
      "scriptFile": "__init__.py",
      "bindings": [
        {
          "type": "cosmosDBTrigger",
          "name": "documents",
          "direction": "in",
          "leaseCollectionName": "leases",
          "connectionStringSetting": "CosmosDbConnectionString", // This is an App Setting name
          "databaseName": "YourDbName",
          "collectionName": "YourContainerName",
          "createLeaseCollectionIfNotExists": true
        }
      ]
    }
    ```
4.  **Reference the Secret in Terraform:** In your `azurerm_function_app` resource, you will now create the `CosmosDbConnectionString` app setting. Instead of a plaintext value, you will use a special syntax to reference the secret in Key Vault.
    ```hcl
    # In your modules/functions/main.tf within the azurerm_function_app resource
    app_settings = {
      // ... other settings
      "CosmosDbConnectionString" = "@Microsoft.KeyVault(SecretUri=${module.key_vault.secret_uri_for_cosmos_connection_string})"
    }
    ```

### Step 4: Deploy the Application Code

Once the infrastructure has been successfully deployed with `terraform apply`, you can deploy your Python code from this folder.

1.  **Use the Core Tools:** From the `functions/` directory, run the publish command:
    ```bash
    func azure functionapp publish <your-function-app-name-from-terraform>
    ```

By following these steps, you ensure a clean separation of concerns between your infrastructure (Terraform) and your application (Python), while building a secure, scalable, and maintainable system.