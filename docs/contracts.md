# Project Contracts & Interfaces
**Version: 2.0**
**Last Updated:** 2025-10-25 

This document defines the protocols and data formats that all components of the Mine Disaster Response system must adhere to. The system has evolved from a trilateration-based model to a **BLE Fingerprinting** model. This version reflects that new architecture.

## 1. Communication Protocol Contract

-   **Physical Devices (ESP32) -> RPi Gateway:** Communication will be done via **LoRa radio packets**.
-   **Simulator -> RPi Gateway:** Communication will be done via **UDP packets** to port `5000`.
-   **RPi Gateway -> Azure Cloud:** Communication will be done via **MQTT** using the Azure IoT Device SDK for Python.
-   **Azure Cloud -> RPi Gateway:** Commands will be sent via **Azure IoT Hub Cloud-to-Device (C2D) messages**.
-   **Positioning Algorithm -> Gateway Code:** Integration will be done via a direct Python function call within the RPi gateway script.

## 2. Data Schema Contracts

### 2.1. Device-to-Gateway Telemetry (UDP/LoRa Packet)

This is the primary data packet sent from a miner device (real or simulated) to the RPi gateway.

```json
{
  "device_id": "miner_01",
  "timestamp": 1727832865,
  "ble_readings": {
    "beacon_001": -65.4,
    "beacon_005": -72.1,
    "beacon_010": -85.3
  },
  "imu_data": {
    "accel_x": 0.12,
    "accel_y": -0.05,
    "accel_z": 9.81,
    "gyro_x": 0.01,
    "gyro_y": 0.02,
    "gyro_z": 0.03
  },
  "battery": 85,
  "position": {
    "x": 10.5,
    "y": 20.1
  }
}
```
**Note:** The `position` field is included by the simulator for validation purposes only. It is not expected to be sent by real hardware.

### 2.2. Gateway-to-Cloud Miner Update (Azure IoT Hub Message)

This is the enriched message the gateway sends to Azure IoT Hub for each processed device packet.

```json
{
  "device_id": "miner_01",
  "timestamp": "2025-10-25T13:42:16.123Z",
  "device_timestamp": 1727832865,
  "position": {
    "x": 10.5,
    "y": 20.1
  },
  "confidence": 0.85,
  "ble_readings": {
    "beacon_001": -65.4,
    "beacon_005": -72.1,
    "beacon_010": -85.3
  },
  "imu_data": {
    "accel_x": 0.12,
    "accel_y": -0.05,
    "accel_z": 9.81
  },
  "battery": 85
}
```

### 2.3. Gateway-to-Cloud Status (Azure IoT Hub Message)

The RPi gateway's periodic status update to Azure.

```json
{
  "gateway_id": "rpi_mine_entrance",
  "timestamp": "2025-10-25T13:42:16.123Z",
  "status": "operational",
  "miners_tracked": 5
}
```
---
*Note: The following contracts (2.4, 2.5, 3) are forward-looking and represent the target for future development, as they are not fully implemented in `main_v2.py`.*
### 2.4. Cloud-to-Gateway Command (Azure C2D Message)

High-level commands from a cloud dashboard to the RPi gateway.

```json
{
  "command_id": "cmd-20251025-1",
  "command": "set_goal_for_all",
  "target": "SAFE_ZONE"
}
```

### 2.5. Gateway-to-Device Command (LoRa/UDP Packet)

Commands sent from the RPi back to a specific miner device (currently stubbed).

```json
{
  "device_id": "miner_01",
  "command": "move_to",
  "next_step": {
    "x": 11.5,
    "y": 20.8
  }
}
```

## 3. Algorithm Interface Contract

### 3.1. Position Estimation

The ML model for position estimation must be callable via a standardized Python function.

```python
def estimate_miner_position(ble_readings: dict) -> tuple:
    """
    Estimates a miner's position based on a BLE fingerprint.

    Args:
        ble_readings (dict): A dictionary where keys are beacon IDs and values are their RSSI.

    Returns:
        tuple: A tuple containing ((x, y), confidence), where (x,y) are the
               estimated coordinates and confidence is a float from 0.0 to 1.0.
    """
    # ... implementation by ML Team ...
    return (estimated_x, estimated_y), confidence
```

### 3.2. Pathfinding (Future)

The pathfinding algorithm for navigating the mine.

```python
def a_star_pathfinding(start: tuple, goal: tuple, grid: list = None) -> list:
    """
    Calculates the optimal path from a start to a goal coordinate.

    Args:
        start (tuple): The (x, y) starting coordinate.
        goal (tuple): The (x, y) destination coordinate.
        grid (list, optional): A 2D grid representing mine obstacles.

    Returns:
        list: A list of (x, y) tuples representing the path.
    """
    # ... implementation ...
    return calculated_path
```

## 4. Data Logging Contract (SQLite)

Defines the schema for the local `mine_nav.db` database on the RPi gateway, aligned with `main_v2.py`.

### Table: `miner_telemetry`

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary Key |
| device_id | TEXT | Unique ID of the miner device |
| timestamp | TEXT | ISO 8601 UTC time when the record was logged |
| ble_readings | TEXT | **JSON string** of the beacon-to-RSSI dictionary |
| imu_data | TEXT | **JSON string** of the IMU sensor data |
| battery | INTEGER | Battery percentage |
| estimated_x | REAL | The X-coordinate estimated by the positioning model |
| estimated_y | REAL | The Y-coordinate estimated by the positioning model |
| confidence | REAL | The confidence score (0.0-1.0) of the position estimate |

### Table: `navigation_commands`

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary Key |
| device_id | TEXT | The target miner's ID |
| timestamp | TEXT | ISO 8601 UTC time the command was issued |
| command | TEXT | JSON string representing the navigation command |


