# Gateway Architecture and Design Notes

**Last Updated:** 2025-10-25

This document explains the architectural decisions, data flow, and evolution of the Raspberry Pi gateway scripts.

## Core Purpose

The RPi gateway is the bridge between the "on-the-ground" devices in the mine and the Azure cloud backend. It has four primary responsibilities:
1.  **Receive**: Collect raw sensor data from miner devices over the local network.
2.  **Process**: Perform initial processing, such as estimating a miner's position from sensor data.
3.  **Log**: Store all raw and processed data locally for redundancy and debugging.
4.  **Transmit**: Forward enriched data to Azure IoT Hub for analysis, storage, and visualization.

## Evolution from `main.py` to `main_v2.py`

This directory contains two main scripts, representing a significant pivot in the project's localization strategy.

### `main.py` (Legacy - Trilateration)

-   **Concept**: This was the first iteration, based on a theoretical **trilateration/multilateration** model. It assumed we could calculate a miner's position if we knew their distance from several fixed anchor points.
-   **Data Model**: Expected simple packets with a single RSSI value, from which distance would be inferred. The database schema is correspondingly simple, with columns for individual sensor values like `accel_x` and `rssi`.
-   **Limitations**: This approach is notoriously unreliable in complex indoor environments due to signal reflection and obstacles. The logic was largely based on simulation and proved insufficient for a real-world scenario.

### `main_v2.py` (Current - BLE Fingerprinting)

-   **Concept**: This is the current, more robust implementation, designed for **BLE Fingerprinting**. This approach does not try to calculate position directly. Instead, it collects a "fingerprint" of the radio environment (a list of all visible BLE beacons and their signal strengths) and uses a machine learning model to match that fingerprint to a known location.
-   **Data Model**: It is designed to receive a richer JSON payload from devices, containing a `ble_readings` object (e.g., `{"beacon_01": -65, "beacon_02": -78, ...}`). The database schema is updated to store this JSON object directly.
-   **Architectural Improvements**:
    -   **Concurrency**: Uses a `ThreadPoolExecutor` to process messages from multiple miners without getting blocked by network I/O or processing delays. This is essential for scaling.
    -   **Modularity**: The logic is better separated into distinct functions (`init_iot_client`, `process_miner_message`, `update_miner_state`), making it easier to maintain.
    -   **Statefulness**: It introduces an in-memory dictionary `current_miner_states` to hold the latest information for each miner, which is crucial for real-time decision-making (like navigation).

**`main_v2.py` is the active script and should be used for all future development.**

## Key Components in `main_v2.py`

-   **`udp_listener`**: Runs in a dedicated thread. Its only job is to listen for UDP packets and immediately hand them off to the `thread_pool`. This keeps the listener responsive.
-   **`process_miner_message`**: The workhorse function. It runs in the thread pool and handles the entire pipeline for a single message: decoding, position estimation, database logging, and sending to Azure.
-   **`estimate_miner_position`**: **This is currently a stub.** It returns random coordinates. For the project to be complete, this function must be replaced with a real ML model inference call (e.g., loading a trained k-NN or neural network model and using it to predict `(x, y)` from the `ble_readings`).
-   **`NavigationManager`**: A placeholder class intended to manage pathfinding. It would receive a goal (like "go to SAFE_ZONE"), calculate a path using an algorithm like A*, and determine the next step for a miner. This is not fully implemented.
