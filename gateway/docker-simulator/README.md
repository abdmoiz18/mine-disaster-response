# Docker Simulator

## Overview
The Docker simulator provides a containerized environment for testing the Mine Disaster Response system without physical hardware. It simulates ESP32 devices, LoRa communication, and mine conditions.

## Features
- **Miner Device Simulation**: Virtual ESP32 devices with simulated IMU data
- **LoRa Network Emulation**: Simulates LoRa communication with configurable packet loss
- **Scenario Generation**: Creates various disaster scenarios for testing
- **Visual Interface**: Optional web interface for monitoring simulations
- **Integration Testing**: Tests full system integration without hardware dependencies

## Usage
1. Build the Docker image:
   ```bash
   docker build -t mine-disaster-simulator .
   ```
2. Run the simulator:
   ```bash
   docker run -p 8080:8080 mine-disaster-simulator
   ```
3. Access the visualization interface at http://localhost:8080

## Configuration
1. Edit simulator_config.json to adjust simulation parameters
2. Modify scenarios.json to create custom disaster scenarios

## Custom Scenarios

Create your own test scenarios by following this template in scenarios.json:

```json
{
  "scenario_name": "Collapsed_Tunnel_B",
  "miner_count": 5,
  "blocked_paths": [[1,3], [2,3], [3,3]],
  "starting_positions": [[0,0], [4,2], [5,6], [2,7], [8,8]],
  "exit_points": [[9,9]]
}
```

## Integration with RPi Scripts
The simulator can be connected to the actual RPi scripts for testing:

```bash
docker run --network=host -e CONNECT_TO_RPI=true mine-disaster-simulator
```
