# Mine Disaster Response and Navigation System
**Version 2.0**

An Azure-native, IoT-based system for tracking and navigating trapped miners. This project uses BLE fingerprinting for localization, a Raspberry Pi edge gateway, and a cloud backend defined with Terraform and deployed with Docker.

## Project Structure & Team Ownership

| Component | Lead | Description |
| :--- | :--- | :--- |
| [`/terraform`](./terraform/README.md) | Cloud Team | **Infrastructure as Code (IaC)** for all Azure resources (IoT Hub, Stream Analytics, Cosmos DB, Key Vault). |
| [`/gateway/rpi-scripts`](./gateway/rpi-scripts/README.md) | Cloud Team | RPi gateway logic: receives UDP data, logs to SQLite, and forwards to Azure IoT Hub. |
| [`/gateway/docker-simulator`](./gateway/docker-simulator/README.md) | All Teams | Simulates miner movement and generates BLE fingerprint data for local development and testing. |
| [`/algorithms`](./algorithms/README.md) | Data Team | **ML models for position estimation** from BLE fingerprints and pathfinding algorithms (A*). |
| [`/hardware/esp32-firmware`](./hardware/esp32-firmware/README.md) | Hardware Team | Firmware for miner devices, responsible for scanning BLE beacons and transmitting data via LoRa/WiFi. |
| [`/docs`](./docs/contracts.md) | All | **Source of Truth.** Defines all data schemas, API contracts, and communication protocols. |

## Getting Started

1.  **Read the Contracts:** Before doing anything, read [`/docs/contracts.md`](./docs/contracts.md). This defines how all the components talk to each other.
2.  **Deploy the Infrastructure:** The Cloud Team should first use Terraform to deploy the Azure backend. See the [`/terraform/README.md`](./terraform/README.md).
3.  **Run the Simulator & Gateway:** Navigate to the `/gateway` subdirectories to run the simulator and the RPi gateway script for end-to-end testing.

## Core Technologies
- **Edge:** ESP32 (C++), **BLE (for localization)**, LoRa/WiFi (for communication)
- **Gateway:** Raspberry Pi 4, Python, **Docker**, **UDP**, SQLite
- **Intelligence:** **ML-based Position Estimation (Fingerprinting)**, A* Pathfinding
- **Cloud & DevOps:** **Terraform**, Azure IoT Hub, Azure Stream Analytics, Azure Cosmos DB, Azure Key Vault

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

