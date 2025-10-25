# Terraform Infrastructure Architecture

This document provides a detailed architectural overview of the Terraform codebase for the Mine Disaster Response project. Its purpose is to explain what each file does and, more importantly, how they all connect to form a cohesive, automated system for deploying our Azure infrastructure.

## 1. High-Level Philosophy: Modularity and Composition

The architecture of this Terraform project is built on two core principles: **Modularity** and **Composition**.

*   **Modularity:** Each major component of our Azure infrastructure (IoT Hub, Cosmos DB, Stream Analytics) is defined in its own self-contained directory under `modules/`. Think of these modules as reusable "black boxes" or blueprints. The `iot-hub` module, for instance, knows everything about creating a correctly configured IoT Hub, but it knows nothing about Cosmos DB.

*   **Composition:** The files in the root directory (`cloud/terraform/`) are responsible for **composition**. They act as an orchestrator, taking the individual modules (the "black boxes") and wiring them together to build the complete, interconnected system. This is where the output of one module becomes the input for another.

This separation makes the system easier to understand, maintain, and extend.

## 2. The Root Module: The System Orchestrator

The files in the `cloud/terraform/` directory define the overall shape of our deployment.

### `main.tf`
This is the heart of the composition layer. It is the master blueprint that declares which modules to use and how to connect them.

*   **What it does:**
    1.  **Defines the Resource Group:** It starts by declaring the `azurerm_resource_group`, which acts as a logical container for all other resources.
    2.  **Instantiates Modules:** It contains three `module` blocks: `iot_hub`, `cosmos_db`, and `stream_analytics`. Each block is like a function call, telling Terraform to use the blueprint from the corresponding `./modules/` subdirectory.
*   **Key Interconnections:** This file is where the critical "wiring" happens.
    *   The `resource_group_name` for every module is set to `azurerm_resource_group.rg.name`, ensuring all resources are created in the same group.
    *   The `stream_analytics` module's `iot_hub_namespace` input is fed by the `iot_hub` module's output: `module.iot_hub.iot_hub_namespace`.
    *   Similarly, its `cosmos_db_account_name` input is fed by the `cosmos_db` module's output: `module.cosmos_db.account_name`.

    This passing of outputs to inputs is how Terraform builds a dependency graph and understands the relationships between our cloud components.

### `variables.tf`
This file defines the "API" for our entire Terraform project. It lists all the parameters that can be customized by a user.

*   **What it does:** It contains `variable` blocks that define input parameters like `location`, `resource_group_name`, and resource-specific names.
*   **How it works:** Each variable has a `description`, a `type`, and a `default` value. The `default` values are crucial; they mean that a user can run `terraform apply` without configuring anything and still get a working environment.

### `terraform.tfvars`
If `variables.tf` is the API definition, `terraform.tfvars` is the user's implementation.

*   **What it does:** This file allows a user to **override the `default` values** from `variables.tf` without modifying the core logic.
*   **How it works:** Terraform automatically loads any file named `terraform.tfvars` and uses its values. This is how you can easily switch from a free "F1" IoT Hub to a paid "S1" SKU or change the deployment region, simply by editing this file.

### `outputs.tf`
This file defines what information our Terraform project should print to the screen after a successful deployment.

*   **What it does:** It declares `output` blocks that expose useful information from the modules, such as connection strings, hostnames, and keys.
*   **Key Interconnections:** It reaches *into* the modules to pull out their specific outputs. For example, `value = module.iot_hub.service_connection_string` pulls the connection string from the `iot-hub` module so the user can easily copy and paste it into an application.

### `versions.tf`
This file specifies the project's dependencies.

*   **What it does:**
    1.  `required_providers`: It tells Terraform which providers (e.g., `azurerm`) and which versions are needed to run this code.
    2.  `backend "azurerm"`: This (currently commented out) block is critically important for teamwork. It instructs Terraform to store its state file in a shared Azure Storage Account instead of on your local machine, preventing conflicts.

## 3. The Modules: The Reusable Blueprints

The directories in `modules/` contain the detailed blueprints for each individual service.

### `modules/iot-hub/main.tf`
This module is responsible for the Azure IoT Hub.

*   **What it does:**
    *   It defines the primary `azurerm_iothub` resource.
    *   It uses a `data "azurerm_iothub_shared_access_policy"` block. This is a subtle but important point: instead of creating a new policy, it **looks up the existing, built-in `service` policy**. This is a best practice for security and reliability.
*   **Outputs:** It outputs the `hostname` (for devices) and the `primary_connection_string` of the service policy (for backend apps).

### `modules/cosmos-db/main.tf`
This module is responsible for our NoSQL database.

*   **What it does:** It defines three resources that build on each other:
    1.  `azurerm_cosmosdb_account`: The top-level serverless account.
    2.  `azurerm_cosmosdb_sql_database`: The database named `miner_navigation`.
    3.  `azurerm_cosmosdb_sql_container`: The container named `miner_telemetry`, where our data will actually be stored. It also defines the partition key (`/device_id`), which is critical for performance and scalability.
*   **Outputs:** It outputs the `endpoint` URL and the sensitive `primary_key` needed for the application SDK to connect.

### `modules/stream-analytics/`
This is the most complex module, as it acts as the central "glue" connecting the data source (IoT Hub) to the data sink (Cosmos DB).

#### `main.tf`
*   **What it does:**
    *   Defines the `azurerm_stream_analytics_job` itself.
    *   Defines the `azurerm_stream_analytics_stream_input_iothub`, which tells the job to listen to the IoT Hub's event stream.
    *   Defines the `azurerm_stream_analytics_output_cosmosdb`, which tells the job where to write the processed data.
*   **Key Interconnections and "Gotchas":**
    *   **Data Sources:** This module makes heavy use of `data` sources. It takes the *names* of the IoT Hub and Cosmos DB account as input variables and uses `data "azurerm_iothub" "iothub"` and `data "azurerm_cosmosdb_account" "cosmosdb"` to fetch their full details, including their secret keys. This is how it gets the credentials needed to connect to them.
    *   **The `lifecycle` Block (A Critical Bug Fix):** The `lifecycle { ignore_changes = [transformation_query] }` block is a crucial piece of the puzzle.
        *   **The Problem:** We discovered a subtle bug where `terraform apply` would fail with a `404 Not Found` error. The Azure API was reporting that the query inside the job was named `"Transformation"`, but the Terraform provider was trying to find and update a query named `"main"`.
        *   **The Solution:** This `lifecycle` block tells Terraform: "You are responsible for creating the query initially, but **do not ever attempt to update it after creation.**" This allows the initial deployment to succeed and prevents future runs from failing due to this provider-API mismatch. It's a perfect example of how real-world IaC requires handling the quirks of cloud provider APIs.

#### `query.sql`
*   **What it is:** This is not an infrastructure file, but a logic file. It contains the SQL-like query that the Stream Analytics job executes on the incoming data stream.
*   **How it's connected:** The `stream-analytics/main.tf` file loads this query using the `file()` function: `transformation_query = file("${path.module}/query.sql")`. This elegantly separates the infrastructure definition from the data processing logic. The query itself is responsible for transforming the raw JSON from the IoT devices into the structured documents that are saved in Cosmos DB.

---

By structuring the project in this way, we have created a system that is robust, easy to understand, and maintainable. The root module provides a clean, high-level view of the architecture, while the individual modules encapsulate the complex details of each service.
