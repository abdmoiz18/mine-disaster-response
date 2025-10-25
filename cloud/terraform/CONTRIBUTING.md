# Contributing to Infrastructure

All changes to the Terraform infrastructure for this project must be made via a GitHub Pull Request.

## The Process

1.  **Create a New Branch:** Create a new branch for your change (e.g., `feature/add-firewall-rule`).
2.  **Make Your Code Changes:** Edit the Terraform (`.tf`, `.tfvars`) files as needed.
3.  **Run `terraform plan`:** Run `plan` and copy the output.
4.  **Open a Pull Request:** Create a new PR. In the description, **paste the entire output of your `terraform plan`**. This is the most important step. It allows your teammates to review exactly what effect your code change will have on the live infrastructure.
5.  **Review and Merge:** At least one other teammate must review the plan in the PR and approve it. Once approved, the PR can be merged into `main`.
6.  **Apply from `main`:** After merging, pull the latest `main` branch to your local machine, and run `terraform apply` from there. **Only code from the `main` branch should ever be applied to the production environment.**