# RPi Scripts - Edge Gateway

**Last Updated:** 2025-10-25

## Overview

This directory contains the Python scripts for the Raspberry Pi, which acts as the primary edge gateway for the Mine Disaster Response system. Its main responsibility is to receive sensor data from miner devices over the local network, process it, and forward it to Azure IoT Hub for cloud-side monitoring and analysis.

The current implementation, **`main_v2.py`**, is designed to work with a **BLE (Bluetooth Low Energy) fingerprinting** model for indoor localization.

## Features

-   **BLE Fingerprinting Data Ingestion**: Listens for UDP packets containing sensor data, specifically structured for BLE fingerprinting (a dictionary of beacon IDs and RSSI values).
-   **Concurrent Processing**: Uses a thread pool to handle incoming data from multiple miners simultaneously without blocking.
-   **Local Data Logging**: Logs all incoming telemetry and gateway events to a local SQLite database (`mine_nav.db`) for persistence and debugging.
-   **State Management**: Maintains the last known state (position, confidence, etc.) of each miner in memory for real-time operations.
-   **Azure IoT Integration**: Securely connects to Azure IoT Hub to stream processed data, including estimated positions, raw sensor readings, and gateway status updates.
-   **Extensible Navigation (Stubbed)**: Includes a `NavigationManager` and a placeholder for an A* pathfinding algorithm to provide a framework for future command-and-control features.

## Setup and Usage

### Prerequisites

-   Python 3.7+
-   An Azure IoT Hub Device Connection String

### Setup

1.  **Install Dependencies:**
    While a `requirements.txt` is not present, the necessary library is `azure-iot-device`.
    ```bash
    pip install azure-iot-device
    ```

2.  **Set Environment Variable:**
    The gateway requires a connection string to authenticate with Azure IoT Hub. Set this as an environment variable.
    ```bash
    export IOTHUB_DEVICE_CONNECTION_STRING="<Your_Azure_IoT_Hub_Device_Connection_String>"
    ```
    To make this permanent, add the line above to your `~/.bashrc` or `~/.profile` file.

### Running the Gateway

Execute the main script. The gateway will initialize the database, connect to Azure, and start listening for UDP traffic.

```bash
python main_v2.py
```

To test the connection to Azure independently, you can run:
```bash
python test_azure.py
```

## How It Works

1.  The gateway starts a **UDP listener** on port 5000.
2.  The `docker-simulator` (or a real hardware gateway) sends JSON packets to this port.
3.  For each packet received, the `udp_listener` submits a task to a **thread pool**.
4.  The `process_miner_message` function decodes the JSON, logs the raw data to SQLite, and calls `estimate_miner_position` (currently a stub function) to determine the miner's location from the BLE fingerprint.
5.  The processed data, including the estimated position and confidence, is formatted into a new JSON payload and sent to **Azure IoT Hub**.
6.  A separate main loop runs periodically to handle higher-level logic, such as pathfinding and sending status updates.
