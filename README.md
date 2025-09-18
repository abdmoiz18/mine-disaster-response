# Mine Navigation and Disaster Response System

A self-contained edge computing system using Raspberry Pi, LoRa, and ESP32 devices to track and guide trapped miners to safety within a grid-based mine environment. Features real-time localization, strategic pathfinding, and cloud-based monitoring.

## Ì≥Å Project Structure & Team Ownership

| Component | Lead | Description |
| :--- | :--- | :--- |
| [`/hardware/esp32-firmware`](./hardware/esp32-firmware/README.md) | Hardware Team | ESP32 firmware for mobile miner devices (IMU, LoRa). |
| [`/hardware/fixed-anchors`](./hardware/fixed-anchors/README.md) | Hardware Team | ESP32 firmware for fixed anchor nodes (LoRa ranging). |
| [`/gateway/rpi-scripts`](./gateway/rpi-scripts/README.md) | Cloud Team | RPi core brain: Localization Engine, Pathfinding integration, SQLite logging. |
| [`/algorithms`](./algorithms/README.md) | Data Team | Pathfinding (A*) and strategic grouping algorithms for grid navigation. |
| [`/cloud`](./cloud/azure-functions/README.md) | Cloud Team | Lightweight Azure Functions for monitoring and high-level command relay. |
| [`/docs`](./docs/contracts.md) | All | Project contracts, plans, and the predefined mine grid map. |

## Ì∫Ä Getting Started

1.  **Read the Contracts:** Before doing anything, read [`/docs/contracts.md`](./docs/contracts.md). These are the project's rules.
2.  **Setup for your role:** Navigate to your team's directory and follow the detailed README for setup instructions.

## Ì¥ß Core Technologies
- **Edge:** ESP32 (C++), LoRa (SX1276), IMU (MPU-6050)
- **Gateway:** Raspberry Pi 4, Python, SQLite
- **Intelligence:** Custom A* Pathfinding, Strategic Grouping Algorithms
- **Cloud:** Azure IoT Hub, Azure Functions

## Ì≥Ñ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
