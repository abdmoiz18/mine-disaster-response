# Contributor Guidelines

**Last Updated:** 2025-10-25

This document provides guidelines for contributing to the Mine Disaster Response System project.

## A Note for External Observers

Thank you for your interest in our project! Please note that this is a capstone project for a university course with a defined team. As such, **we are not accepting direct code contributions via Pull Requests** from outside the project group.

However, we welcome your feedback and suggestions! If you have an idea, spot a bug, or have a question, please feel free to **open an issue** in the repository.

---

## Internal Team Development Workflow

This section is for project members:

To ensure consistency and quality, all team members must follow this workflow for all changes.

### 1. Create a Feature Branch

All new work, no matter how small, must be done on a dedicated feature branch. Name your branch descriptively.

```bash
# Good branch names
git checkout -b feat/implement-astar-pathfinding
git checkout -b fix/correct-iot-hub-reconnection-logic
git checkout -b docs/update-architecture-diagram
```

### 2. Make Your Changes

Write your code, following the existing style and conventions.

### 3. Update Documentation

If your changes affect a data format, communication protocol, or system architecture, you **must** update the relevant markdown files in the `/docs` folder. The `docs/contracts.md` file is our single source of truth.

### 4. Commit Your Work

Write clear and concise commit messages that explain the "what" and "why" of your change.

```bash
git commit -m "feat: Implement A* pathfinding algorithm"
```

### 5. Create a Pull Request

Push your branch to the remote repository and open a Pull Request against the `main` branch.

-   Assign at least one other team member to review your PR.
-   No PR should be merged without at least one approval.

## Key Development Principles

1.  **The Contract is King**: Before implementing any feature that involves communication between two components, check `docs/contracts.md`. If the contract needs to change, it must be updated and approved as part of your PR.
2.  **Infrastructure as Code (IaC)**: All Azure infrastructure is managed by Terraform. Do not make manual changes to production resources in the Azure Portal. Refer to the `terraform/MANUAL_CHANGES_POLICY.md` for the correct process for experimentation.
3.  **Test with the Simulator**: Before submitting a PR, test your changes against the `docker-simulator`. This is the best way to ensure your gateway logic or cloud components will work with the data format from the hardware.

## Setting up the Full Environment

To run the full software stack for end-to-end testing:

1.  **Deploy the Cloud Backend:**
    *   Navigate to the `/terraform` directory.
    *   Authenticate with Azure (`az login`).
    *   Run `terraform init` and `terraform apply`.
    *   Get the IoT Hub connection string for your device and set it as an environment variable (`export IOTHUB_DEVICE_CONNECTION_STRING=...`).

2.  **Run the Gateway:**
    *   In a new terminal, navigate to `/gateway/rpi-scripts`.
    *   Run `python main_v2.py`.

3.  **Run the Simulator:**
    *   In a second terminal, navigate to `/gateway/docker-simulator`.
    *   Verify the `HOST` IP in `init_simulator_v2.py` matches the IP of the machine running the gateway.
    *   Run `docker-compose up`.

You should now see data flowing from the simulator, through the gateway, and into your Azure IoT Hub.
