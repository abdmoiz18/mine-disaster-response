# RPi Scripts - Edge Gateway

## Overview
This directory contains the Raspberry Pi scripts that serve as the core brain of the Mine Disaster Response system. The RPi acts as an edge server connecting the local mine environment to Azure cloud services.

## Features
- **Localization Engine**: Processes data from fixed anchor nodes to determine miner positions
- **Pathfinding Integration**: Interfaces with pathfinding algorithms to guide miners to safety
- **SQLite Logging**: Local database for storing position data, events, and system logs
- **LoRa Communication**: Manages communication with ESP32 devices through LoRa protocol
- **Azure IoT Integration**: Connects to Azure IoT Hub for cloud monitoring and commands

## Setup Instructions
1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure the environment variables in .env
3. Run:
   ```bash
   python main.py
   ```

