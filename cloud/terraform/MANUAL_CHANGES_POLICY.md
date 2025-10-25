# Policy on Manual Azure Changes

**Last Updated:** 2025-10-25
**Owner:** abdmoiz18

This document defines the policy for making changes to our Azure environment. Its purpose is to protect the integrity of our Infrastructure as Code (IaC) setup and prevent **configuration drift**, which occurs when the real-world state of our infrastructure in Azure no longer matches the state defined in our Terraform code.

## The Golden Rule

**DO NOT** make manual changes to any Azure resource that is managed by Terraform.

If a resource is defined in a `.tf` file, its configuration must only be changed through the official Terraform workflow:
1.  **Code:** Modify the Terraform code in your branch.
2.  **Plan:** Run `terraform plan` to review the intended changes.
3.  **Review:** Open a Pull Request for peer review.
4.  **Apply:** After approval and merge, run `terraform apply` to enact the changes.

---

## Part 1: Changing Existing Services

### The "Don't" List: Actions to Avoid

-   **Don't** use the Azure Portal to change the SKU, size, tier, or configuration of a Terraform-managed resource.
-   **Don't** use the Azure CLI (`az`) to update a resource's properties (e.g., `az vm update`).
-   **Don't** change firewall rules, access policies, or networking settings through the portal for resources managed by Terraform.

**Why?** The next time `terraform apply` is run, Terraform will see the discrepancy between its state file and the actual state. It will **overwrite your manual changes** to enforce the configuration defined in the code. This can lead to unexpected outages or reversion of a critical fix.

### Handling "Break-Glass" Emergencies

We recognize that in a critical incident, a rapid manual change might be necessary to restore service.

**Procedure:**
1.  **Declare Intent:** Announce in the team channel that you are making an emergency manual change.
2.  **Apply the Fix:** Make the minimum necessary change in the Azure Portal or via Azure CLI to mitigate the issue.
3.  **IMMEDIATELY Reconcile:** As soon as the incident is stable, you **must** update the Terraform code to match the manual change you made.
    *   For example, if you changed a Cosmos DB capacity setting from `1000` to `1200` RU/s in the portal, you must immediately open a PR to change the corresponding value in the `.tf` file to `1200`.
4.  **Verify Reconciliation:** Run `terraform plan`. The plan should report `No changes. Your infrastructure matches the configuration.` This confirms the code now reflects the real-world state.

Failure to reconcile will result in the emergency fix being silently reverted during the next deployment.

---

## Part 2: Creating New Services

### The Challenge: Prototyping and Integration Testing

It can be efficient to create new services in the portal to experiment or verify that they integrate correctly with the existing (Terraform-managed) infrastructure. This is acceptable, but **only if a strict process is followed**.

### The "Do" List: Safe Prototyping Workflow

1.  **Isolate Your Work:**
    *   **DO** create a **new, temporary resource group** for your experimentation. Name it clearly, e.g., `rg-prototype-my-feature-abdmoiz18`.
    *   **DO NOT** create new, unmanaged resources inside a resource group that is managed by Terraform.

2.  **Prototype and Verify:**
    *   Create your new services (e.g., a VM, a new Function App) inside this temporary resource group.
    *   Configure them and test their integration with our existing, Terraform-managed services. For example, check if your prototype VM can connect to the production Cosmos DB.

3.  **Formalize as Code:**
    *   Once you are satisfied with the prototype, the next step is to **write the Terraform code** for the new resources. Create a new module or add to an existing one to define the resources you just built manually.

4.  **Import, Don't Recreate:**
    *   This is the most critical step. Instead of deleting the manual resource and letting Terraform create a new one, you will use the `terraform import` command. This tells Terraform to "adopt" the existing resource and bring it under its management.
    *   **Example:**
        ```bash
        # 1. Get the Azure Resource ID of your manually created resource
        AZURE_ID="/subscriptions/your-sub-id/resourceGroups/rg-prototype.../providers/Microsoft.Storage/storageAccounts/yourteststorage"

        # 2. Define the resource in your .tf file
        # resource "azurerm_storage_account" "new_account" { ... }

        # 3. Run the import command
        terraform import azurerm_storage_account.new_account $AZURE_ID
        ```

5.  **Reconcile and Finalize:**
    *   After the import, run `terraform plan`.
    *   Terraform will likely show differences between the configuration of the imported resource and the code you wrote.
    *   **Adjust your `.tf` code** until the plan is clean and shows only the intended configuration.
    *   You have now successfully and safely migrated a manual resource to be fully managed by IaC.

6.  **Clean Up:**
    *   Delete the temporary resource group (`rg-prototype-...`) you created in Step 1.

By following this process, we gain the speed of manual prototyping while ensuring that every production resource ultimately becomes part of our auditable, repeatable, and reliable infrastructure-as-code repository.