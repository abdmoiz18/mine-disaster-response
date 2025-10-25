# System Architecture

**Last Updated:** 2025-10-25

This document provides a high-level overview of the entire Mine Disaster Response system, showing how the different components interact.

## System Flow Diagram

```mermaid
graph TD
    subgraph "Mine Environment"
        A[ESP32 Miner Device] -- BLE Scan --> B((BLE Beacons));
        A -- "LoRa / WiFi" --> C[Raspberry Pi Gateway];
    end

    subgraph "Development & Testing"
        D[Docker Simulator] -- "UDP" --> C;
    end

    subgraph "Edge Gateway (Raspberry Pi)"
        C -- "1. Receives UDP/LoRa" --> E{Gateway Logic (main_v2.py)};
        E -- "2. Logs to" --> F[(mine_nav.db)];
        E -- "3. Uses ML Model" --> G[Positioning Model];
        E -- "4. Sends to Cloud" --> H{Azure IoT Hub};
    end

    subgraph "Azure Cloud (Managed by Terraform)"
        H -- "Device Data" --> I[Stream Analytics];
        I -- "Outputs To" --> J[(Cosmos DB)];
        K[Azure Functions] -- "Monitors/Triggers on" --> J;
    end

    style A fill:#D6EAF8,stroke:#333,stroke-width:2px
    style C fill:#D5F5E3,stroke:#333,stroke-width:2px
    style H fill:#FADBD8,stroke:#333,stroke-width:2px
```

## Component Breakdown

1.  **Miner Device (ESP32):**
    *   The physical hardware carried by a miner.
    *   It does **not** know its own location.
    *   Its job is to scan for nearby BLE beacons and transmit a "fingerprint" (a list of beacon IDs and their signal strengths) back to the gateway.

2.  **Raspberry Pi Gateway:**
    *   The central brain on the edge.
    *   It runs the `main_v2.py` script.
    *   It listens for data from miner devices.
    *   It uses a trained Machine Learning model to estimate a miner's `(x, y)` position from the BLE fingerprint.
    *   It logs all data locally to a SQLite database for redundancy.
    *   It forwards the enriched data (including the estimated position) to Azure IoT Hub.

3.  **Docker Simulator:**
    *   A development tool that runs on a local machine.
    *   It perfectly mimics the data packets sent by the real ESP32 devices, allowing for full end-to-end testing of the gateway and cloud infrastructure without any physical hardware.

4.  **Azure Infrastructure (Provisioned by Terraform):**
    *   **IoT Hub:** The secure entry point for all data into the cloud.
    *   **Stream Analytics:** A service that processes the data stream in real-time. For example, it could filter for low-battery alerts or check if a miner has entered a danger zone.
    *   **Cosmos DB:** A NoSQL database where the final, processed data is stored for long-term analysis and for use by other applications (like a web dashboard).
