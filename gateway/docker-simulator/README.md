# Docker Simulator for Mine Disaster Response

**Last Updated:** 2025-10-25

## Overview

This simulator provides a containerized environment to generate and transmit mock sensor data for the Mine Disaster Response system, removing the need for physical ESP32 devices during development and testing.

The current version (`init_simulator_v2.py`) simulates multiple miners moving within a 2D grid. For each miner, it calculates a realistic BLE (Bluetooth Low Energy) RSSI fingerprint based on their proximity to a set of fixed beacons. This data, along with simulated IMU readings, is then transmitted over UDP to a specified gateway, mimicking the data flow from real devices in the field.

## Features

-   **Dynamic Miner Simulation**: Simulates multiple miners moving independently based on kinematic equations.
-   **BLE Fingerprinting**: Generates realistic RSSI values from multiple beacons based on a log-distance path loss model and simulated noise.
-   **UDP Data Transmission**: Sends JSON-formatted sensor data packets to a configurable network endpoint.
-   **Containerized Environment**: Uses Docker and Docker Compose for easy, consistent, and isolated execution.
-   **Configurable**: Key parameters like gateway IP, port, and number of miners can be easily modified.

## Usage

This simulator is designed to be run with Docker Compose, which reads the configuration from `docker-compose.yml`.

### Prerequisites

-   Docker
-   Docker Compose

### Running the Simulator

1.  **Navigate to this directory:**
    ```bash
    cd gateway/docker-simulator
    ```

2.  **Run the simulator in the foreground:**
    This will build the image if it doesn't exist and start the container. You will see the log output directly in your terminal.
    ```bash
    docker-compose up
    ```

3.  **Run the simulator in the background (detached mode):**
    ```bash
    docker-compose up -d
    ```

4.  **To stop the simulator:**
    If running in the foreground, press `Ctrl+C`. If running in detached mode:
    ```bash
    docker-compose down
    ```

## Configuration

You can configure the simulation in two ways:

1.  **For persistent changes, edit the Python script:**
    Modify the configuration variables at the top of `init_simulator_v2.py`:
    -   `HOST`: The IP address of the gateway server receiving the data.
    -   `PORT`: The port the gateway server is listening on.
    -   `NUM_MINERS`: The number of miners to simulate.
    -   `GRID_WIDTH`/`GRID_LENGTH`: The dimensions of the simulated mine area.
    -   `BLE_BEACONS`: The location and transmission power of fixed beacons.

2.  **For temporary overrides, use the `docker-compose.yml` file:**
    Uncomment and edit the `command` line in `docker-compose.yml` to override the default `HOST` and `PORT` when the container starts.
    ```yaml
    services:
      mine-simulator:
        # ...
        # You can override the default host/port here
        command: ["python", "init_simulator_v2.py", "192.168.1.100", "5000"]
    ```
    Then, run `docker-compose up` to apply the changes.
