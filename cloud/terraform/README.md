# Mine Disaster Response - Cloud Infrastructure (Terraform)

Welcome to the infrastructure codebase for the Mine Disaster Response project. This directory contains all the Terraform code used to define, deploy, and manage the entire Azure cloud backend.

This document is your guide. Its goal is to be the single source of truth for you and your teammates. If you forget everything about Terraform in six months, this README should be enough to get you back up to speed.

## 1. What is This? The "Blueprint" for Our Cloud

Think of this code as the **official blueprint or schematic for our Azure infrastructure.**

Instead of clicking through the Azure Portal to create resources like the IoT Hub, Cosmos DB, and Stream Analytics job, we write code to declare what we want. Terraform then reads this code and makes Azure match our blueprint. This practice is called **Infrastructure as Code (IaC)**.

Your analogy was perfect: **Terraform is to our cloud infrastructure what Git is to our source code.**

## 2. Why Are We Using Terraform? (The "Why Bother?")

On the surface, this might feel like overkill for an ECE project. However, using Terraform elevates our project from a simple prototype to a professional-grade, manageable system. Here’s the value it provides:

*   **The "Oh No, I Deleted It" Button Becomes the "No Worries" Button:** If you accidentally delete the Cosmos DB account a week before your final presentation, you don't panic. You come to this directory, run `terraform apply`, and Terraform will perfectly recreate it from the blueprint in minutes.
*   **Perfect, Automatic Documentation:** This code **is** your architectural documentation. It's not a diagram that can go stale; it's a precise, always-up-to-date definition of every resource and setting.
*   **Fearless Experimentation:** Want to test a different IoT Hub SKU? Change one line in a `.tfvars` file, run `terraform apply`, and then change it back when you're done. The risk of breaking your working setup is virtually zero.
*   **Collaboration:** With the infrastructure defined as code, you and your teammates can review, comment on, and approve infrastructure changes using Pull Requests, just like you do with Python code.

## 3. Project Structure

This project uses a standard, modular Terraform structure.

```
.
├── main.tf                 # The main entry point. Connects all the modules together.
├── variables.tf            # Defines the input variables our configuration needs.
├── terraform.tfvars        # **Your settings file.** You customize your deployment here.
├── outputs.tf              # Declares what information to output after a deployment (e.g., hostnames, keys).
├── versions.tf             # Defines the Terraform and provider versions required.
├── README.md               # This file.
│
└── modules/                # Directory for reusable components ("black boxes").
    ├── cosmos-db/          # Blueprint for our Cosmos DB Account, Database, and Container.
    ├── iot-hub/            # Blueprint for our IoT Hub.
    └── stream-analytics/   # Blueprint for our Stream Analytics Job, its inputs, and outputs.
```

## 4. The Essential Workflow: Your Four Key Commands

You only need to know four commands to be effective. **Always run them from this directory (`cloud/terraform/`).**

1.  `terraform init`
    *   **What it does:** Initializes the project. It reads your `versions.tf` file and downloads the necessary "plugins" (like the `azurerm` provider).
    *   **Analogy:** This is the `pip install -r requirements.txt` or `npm install` for your infrastructure.
    *   **When to run it:** You only need to run this once when you first set up the project, or whenever you change the provider versions in `versions.tf`.

2.  `terraform plan`
    *   **What it does:** This is a **dry run**. Terraform reads your code, compares it to the live infrastructure in Azure, and shows you exactly what it *would* do if you applied the changes. It will tell you what will be `created`, `changed`, or `destroyed`.
    *   **This is the most important command for safety.** Always run `plan` and review the output before you `apply`.

3.  `terraform apply`
    *   **What it does:** Executes the plan. It performs the actions that `plan` proposed. It will ask for your confirmation before proceeding.
    *   **This is the "Go" button.** It makes the live cloud environment match the blueprint.

4.  `terraform destroy`
    *   **What it does:** Deletes **every single resource** managed by this Terraform configuration.
    *   **Use with extreme caution.** This is useful for tearing down the environment to save costs, but be aware that it is irreversible.

## 5. Getting Started: How to Use This Code

Here’s how a new team member can get up and running.

**Prerequisites:**
1.  Install the [Terraform CLI](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli).
2.  Install the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli).
3.  Log in to your Azure account by running `az login` in your terminal.

**Steps:**
1.  Open a terminal and navigate to this directory: `cd mine-disaster-response/cloud/terraform`.
2.  Run `terraform init` to initialize the project and download the Azure provider.
3.  Run `terraform plan`. Since our code is now perfectly synced with the live Azure resources, you should see the message: **`No changes. Your infrastructure matches the configuration.`** This confirms that your setup is correct.
4.  **To make a change:** Open `terraform.tfvars` and add a new tag, for example: `Test = "true"`. Run `terraform plan` again. You will now see a plan to `update` your resources to add this new tag. Run `terraform apply` to execute it.

## 6. Important Notes & "Gotchas" for This Project

This section captures the key lessons learned during the setup process.

### The `lifecycle { ignore_changes }` Block is Critical

In `modules/stream-analytics/main.tf`, you will find this block:
```hcl
lifecycle {
  ignore_changes = [
    transformation_query,
  ]
}
```
**Why is this here?** We discovered that the Azure API for Stream Analytics has a quirk. The Terraform provider tries to update the job's query by referencing a component named `"main"`, but the portal had named our query `"Transformation"`. This caused a `404 Not Found` error during `apply`. This `lifecycle` block tells Terraform: "Do not attempt to manage the query. Even if the local `query.sql` file is different, ignore it and never try to change it." This allows our `apply` to succeed.

### Remote State: A Must-Do for Teamwork

In `versions.tf`, the `backend "azurerm"` block is commented out. Terraform keeps a "state file" (`terraform.tfstate`) to track the link between your code and the live resources. By default, this file is on your local machine.

**Problem:** If you and a teammate both make changes, you will have conflicting state files, which is a nightmare to resolve.

**Solution:** Before you do any more work as a team, you must configure this remote backend. It tells Terraform to store the state file in a central, shared Azure Storage Account.
1.  Follow this [official HashiCorp tutorial](https://developer.hashicorp.com/terraform/tutorials/azure/azure-storage-account) to create the storage account.
2.  Uncomment the `backend "azurerm"` block in `versions.tf`.
3.  Fill in the correct `storage_account_name`.
4.  Run `terraform init` again. It will ask if you want to copy your existing local state to the new backend. Say yes.

---
This document should serve as a strong foundation. If you follow these steps and principles, you will be able to manage this project's infrastructure safely and effectively for the rest of your capstone.
