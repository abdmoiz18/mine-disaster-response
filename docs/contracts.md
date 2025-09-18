# Project Contracts & Interfaces
Version: 1.0

This document defines the protocols and data formats that all components of the Mine Navigation System must adhere to. Any change to this document requires a team-wide discussion and a version increment.

## 1. Communication Protocol Contract

- **ESP32 Devices (Miners & Anchors) -> RPi Gateway:** Communication will be done via **LoRa radio packets** using a predefined frequency and spreading factor (SF).
- **RPi Gateway -> Azure Cloud:** Communication will be done via **MQTT** using the Azure IoT Device SDK for Python.
- **Azure Cloud -> RPi Gateway:** Commands will be sent via **Azure IoT Hub Cloud-to-Device messages**.
- **Data Team Algorithm -> Gateway Code:** Integration will be done via **direct Python function calls** within the RPi.

## 2. Data Schema Contracts

### 2.1. Device-to-Gateway Telemetry (LoRa Packet)

All Miner and Anchor devices must send data in the following JSON format.

#### Miner Device Telemetry:
```json
{
  "device_id": "miner_01",
  "timestamp": 1727832865,
  "accel_x": 0.12,
  "accel_y": -0.05,
  "accel_z": 9.81,
  "gyro_x": 0.01,
  "gyro_y": 0.02,
  "gyro_z": 0.03,
  "rssi": -45,
  "battery": 85
}
```

#### Fixed Anchor Beacon:
```json
{
  "device_id": "anchor_entrance",
  "timestamp": 1727832865,
  "fixed_x": 1,
  "fixed_y": 1,
  "rssi": -70
}
```

### 2.2. Gateway-to-Device Command (LoRa Packet)

Commands sent from the RPi back to a specific miner device.

```json
{
  "device_id": "miner_01",
  "command": "navigate",
  "path": [
    {"x": 1, "y": 1},
    {"x": 1, "y": 2},
    {"x": 2, "y": 2}
  ],
  "next_instruction": "Move North to 1,2"
}
```

### 2.3. Gateway-to-Cloud Status (Azure IoT Hub Message)

The RPi's periodic status update to Azure.

```json
{
  "gateway_id": "rpi_mine_entrance",
  "timestamp": 1727832865,
  "status": "active",
  "miners_connected": 3,
  "last_calculated_strategy": "rally_p1_p2"
}
```

### 2.4. Cloud-to-Gateway Command (Azure IoT Hub Message)

High-level commands from the cloud dashboard to the RPi.

```json
{
  "command_id": 101,
  "command": "set_safe_zone",
  "grid_x": 15,
  "grid_y": 7
}
```

## 3. Algorithm Interface Contract

The Data Team's pathfinding code must be callable via a standardized Python function interface.

#### Function Signature

```python
def solve_maze_strategically(mine_grid, miner_dict, safe_zone):
    """
    Calculates optimal paths for all miners based on a chosen strategy.

    Args:
        mine_grid (list of list of int): A 2D grid representing the mine. 0=path, 1=wall.
        miner_dict (dict): A dictionary where keys are miner IDs and values are their current grid coordinates (x, y).
        safe_zone (tuple): The (x, y) coordinate of the safe zone.

    Returns:
        dict: A dictionary where keys are miner IDs and values are a list of (x, y) tuples representing the path to the safe zone.
    """
    # ... implementation by Data Team ...
    return calculated_paths
```

## 4. Data Logging Contract

### Table : Miner Telemetry


| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary Key | 
| timestamp | TEXT | ISO 8601 UTC time | 
| device_id | TEXT | Miner ID |
| accel_x | REAL | X-axis acceleration |
| accel_y | REAL | Y-axis acceleration |
| accel_z | REAL | Z-axis acceleration |
| gyro_x | REAL | X-axis rotation |
| gyro_y | REAL | Y-axis rotation |
| gyro_z | REAL | Z-axis rotation |
| rssi | INTEGER | Signal strength |
| battery | INTEGER | Battery percentage |


### Table : Commands


| Column | Type | Description |
|--------|------|-------------| 
| id | INTEGER | Primary Key |
| timestamp | TEXT | ISO 8601 UTC time |
| device_id | TEXT | Target Miner ID |
| command | TEXT | Command type (e.g., 'navigate') |
| path | TEXT | JSON-stringified list of path coordinates |


## How to Use This File:

1.  **For the Hardware Team:** You will look at **Section 2.1** to know exactly what JSON format to make their ESP32 devices send.
2.  **For the Data Team:** You will look at **Section 3** to know the exact function name, input parameters, and output format you must provide.
3.  **For Cloud/Gateway Team:** You will use:
    - **Section 2.1** to parse incoming LoRa data.
    - **Section 2.2** to format commands to send back to devices.
    - **Section 2.3 and 2.4** to configure Azure IoT Hub messaging.
    - **Section 4** to design your SQLite database tables.
4.  **For Everyone:** This is the document to point to during integration. If a device is sending the wrong data format, you can point to Section 2.1. If the algorithm returns an error, you can point to Section 3.


