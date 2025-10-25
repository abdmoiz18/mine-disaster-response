# Simulator Architecture and Design Notes

**Last Updated:** 2025-10-25

This document explains the design choices, data flow, and evolution of the simulator.

## Core Purpose

The primary goal of this simulator is to produce a realistic stream of sensor data that the main gateway (`rpi_main_v2.py` or similar) can ingest. This allows for end-to-end testing of the cloud pipeline (Gateway -> IoT Hub -> Stream Analytics -> Cosmos DB) without needing to flash and manage physical hardware.

The simulator sends data via **UDP**, which is a lightweight, connectionless protocol suitable for sending frequent sensor updates where the loss of an occasional packet is acceptable.

## Data Flow

1.  **Initialization**: The `run_simulation` function starts, creating a `MinerSimulator` object for each of the `NUM_MINERS`. Each miner is given a random starting position.

2.  **Simulation Loop (every `SEND_INTERVAL` seconds)**:
    a.  **Update Position**: Each miner's position is updated using kinematic equations (`s = s + v*dt`). Velocity and acceleration are adjusted randomly to simulate wandering movement.
    b.  **Generate BLE Readings**: For a miner's current position, the script calculates the simulated RSSI value from every beacon defined in `BLE_BEACONS`. This is done using a path-loss model, which means the signal gets weaker with distance. Random noise is added to make it more realistic.
    c.  **Generate Packet**: The `generate_miner_data` function assembles a JSON object containing the device ID, timestamp, the BLE readings, simulated IMU data, and battery level.
    d.  **Transmit**: The JSON packet is encoded and sent via a UDP socket to the configured `HOST` and `PORT`.

## Evolution from `init_simulator.py` to `init_simulator_v2.py`

You will notice two simulator scripts in this directory. This reflects an important evolution in the project's approach to indoor navigation.

### `init_simulator.py` (Legacy)

-   **Method**: Based on **trilateration with fixed anchors**.
-   **How it Worked**: It simulated a few fixed "anchor" devices and "miner" devices. It assumed that by measuring the RSSI (signal strength) from three or more known anchor points, you could calculate the miner's position.
-   **Data Sent**: It sent separate, simple packets for each miner and each anchor.
-   **Limitation**: This approach is often inaccurate in complex indoor environments due to signal reflection (multipath) and obstruction. The simulation was too simplistic.

### `init_simulator_v2.py` (Current)

-   **Method**: Based on **BLE Fingerprinting**.
-   **How it Works**: This is a more robust and modern approach. Instead of trying to calculate position directly from signal strength, it uses machine learning. The simulator generates a "fingerprint" for each miner at its location—a dictionary of beacon IDs and their corresponding RSSI values (`{'beacon_001': -75, 'beacon_005': -68, ...}`).
-   **Data Sent**: It sends one comprehensive packet per miner that includes this rich BLE fingerprint. This is the data a machine learning model would use to predict location.
-   **Improvement**: This simulation is far more realistic and provides the exact kind of data needed for a fingerprinting-based ML model. The movement simulation is also more advanced, using velocity and acceleration.

The project has standardized on `init_simulator_v2.py`, which is why it is the default script in the `Dockerfile` and `docker-compose.yml`.
