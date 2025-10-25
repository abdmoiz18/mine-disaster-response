# Contributing Guide

Thank you for your interest in contributing to the Mine Disaster Response System. Following these guidelines helps to maintain the quality and consistency of the codebase.

## Development Workflow

1.  **Create a Feature Branch:** All new work should be done on a feature branch, named descriptively.
    ```bash
    git checkout -b feature/add-astar-pathfinding
    ```

2.  **Make Your Changes:** Write your code, following the existing style.

3.  **Update Documentation:** If your changes affect a contract or architecture, you **must** update the relevant markdown files in the `/docs` folder. The `contracts.md` file is the source of truth.

4.  **Commit Your Work:** Write clear and concise commit messages.
    ```bash
    git commit -m "feat: Implement A* pathfinding algorithm"
    ```

5.  **Create a Pull Request:** Push your branch to the remote and open a Pull Request against the `main` branch. Provide a clear description of the changes you've made.

## Key Principles

### 1. The Contract is King

Before implementing any feature that involves communication between two components, check `docs/contracts.md`. If the contract needs to change, update it in your PR so it can be reviewed. **Do not write code that violates the contract.**

### 2. Infrastructure as Code (IaC)

All Azure infrastructure is managed by Terraform. **Do not make manual changes to Terraform-managed resources in the Azure Portal.** If you need to experiment, create temporary resources and then formalize them in Terraform later. See `terraform/MANUAL_CHANGES_POLICY.md`.

### 3. Test with the Simulator

Before assuming your code works, test it against the `docker-simulator`. This ensures that your gateway logic or cloud components can correctly process the data that will eventually come from the real hardware.

## Setting up the Full Environment

To run the full software stack locally:

1.  **Deploy the Cloud Backend:**
    *   Navigate to the `/terraform` directory.
    *   Authenticate with Azure (`az login`).
    *   Run `terraform init` and `terraform apply`.
    *   Get the IoT Hub connection string for your device and set it as an environment variable (`export IOTHUB_DEVICE_CONNECTION_STRING=...`).

2.  **Run the Gateway:**
    *   In a terminal, navigate to `/gateway/rpi-scripts`.
    *   Run `python main_v2.py`.

3.  **Run the Simulator:**
    *   In a second terminal, navigate to `/gateway/docker-simulator`.
    *   Verify the `HOST` IP in `init_simulator_v2.py` matches the IP of the machine running the gateway.
    *   Run `docker-compose up`.

You should now see data flowing from the simulator, through the gateway, and into your Azure IoT Hub.
