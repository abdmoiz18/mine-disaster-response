# Quickstart Guide - Mine Disaster Response System
**Version 2.0** | **Last Updated:** 2025-11-15

Welcome! This guide will get you from zero to a fully running Mine Disaster Response system in under 30 minutes. Whether you're setting up for local development or deploying to Azure, we've got you covered.

---

## 🎯 What You'll Accomplish

By the end of this guide, you'll have:
- ✅ A simulated mine with 5 miners moving through a 30×30 meter grid
- ✅ 12 BLE beacons tracking miner positions
- ✅ A Raspberry Pi gateway processing telemetry data
- ✅ A live web dashboard showing real-time miner positions
- ✅ (Optional) Full Azure cloud integration with IoT Hub and Cosmos DB

---

## 📋 Prerequisites

### Required Software
- **Python 3.7+** - [Download here](https://www.python.org/downloads/)
- **Docker & Docker Compose** - [Download here](https://www.docker.com/products/docker-desktop)
- **Git** - [Download here](https://git-scm.com/downloads)

### Optional (for Azure deployment)
- **Azure CLI** - [Download here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- **Terraform** - [Download here](https://www.terraform.io/downloads.html)
- **Azure Subscription** - [Sign up here](https://azure.microsoft.com/free/)

### Hardware (for production deployment)
- **Raspberry Pi 4** (2GB+ RAM recommended)
- **ESP32 Development Boards** (for real miner devices)
- **BLE Beacon Hardware** (optional, can use simulator)

### Check Your Installation

```bash
python --version    # Should show 3.7+
docker --version    # Should show 20.10+
git --version       # Should show 2.x+
```

---

## 🚀 Quick Start: Local Development (No Azure)

**Time Estimate:** 15-20 minutes

This section gets the core system running on your local machine without any cloud dependencies.

### Step 1: Clone and Navigate to the Repository

```bash
git clone https://github.com/abdmoiz18/mine-disaster-response.git
cd mine-disaster-response
```

**Expected Output:**
```
Cloning into 'mine-disaster-response'...
remote: Enumerating objects: 156, done.
remote: Total 156 (delta 0), reused 0 (delta 0)
Receiving objects: 100% (156/156), 45.23 KiB | 1.51 MiB/s, done.
```

---

### Step 2: Install Gateway Dependencies

```bash
# Navigate to the gateway scripts directory
cd gateway/rpi-scripts

# Install Python dependencies
pip install azure-iot-device
```

**Expected Output:**
```
Successfully installed azure-iot-device-2.x.x
```

**Note:** The `azure-iot-device` package is required even for local testing. The gateway will skip Azure connection if the environment variable is not set.

---

### Step 3: Start the Simulator

Open a **new terminal window** and run:

```bash
# Navigate to the simulator directory
cd gateway/docker-simulator

# Start the Docker container
docker-compose up
```

**Expected Output:**
```
Creating mine-simulator ... done
Attaching to mine-simulator
mine-simulator    | Starting BLE fingerprinting simulation with 5 miners
mine-simulator    | Grid : 30X30 with 12 BLE beacons
mine-simulator    | Sending to 192.168.137.100:5000 every 5 seconds.
mine-simulator    | Sent miner_01: pos(12.3, 8.7) with 8 BLE readings
mine-simulator    | Sent miner_02: pos(15.1, 22.4) with 7 BLE readings
...
```

**⚠️ Important:** Keep this terminal window open. The simulator needs to run continuously.

**Troubleshooting:**
- If you see "port 5000 already in use", another service is using that port. Stop it or modify `docker-compose.yml` to use a different port.
- If Docker daemon isn't running, start Docker Desktop first.

---

### Step 4: Configure the Gateway

The gateway needs your machine's local IP to receive data from the simulator.

**Find Your Local IP:**

**On Windows:**
```bash
ipconfig
# Look for "IPv4 Address" under your active network adapter
```

**On Mac/Linux:**
```bash
ifconfig
# Look for "inet" address (usually 192.168.x.x or 10.x.x.x)
```

**Update Simulator Configuration:**

Edit `gateway/docker-simulator/init_simulator_v2.py`:

```python
# Line 16 - Change this to your local machine's IP
HOST = '192.168.1.XXX'  # Replace XXX with your actual IP
```

**Restart the simulator** after making this change (Ctrl+C in the simulator terminal, then `docker-compose up` again).

---

### Step 5: Start the RPi Gateway

Open another **new terminal window**:

```bash
# Navigate to the gateway scripts directory
cd gateway/rpi-scripts

# Run the gateway
python main_v2.py
```

**Expected Output:**
```
Starting BLE Fingerprinting Gateway...
Starting UDP Listener...
Listening for UDP messages on 0.0.0.0:5000
IoT Client not initiated. Skipping message.  # This is OK for local testing
Sent miner_01: pos(12.3, 8.7) with 8 BLE readings
Updated miner_id : miner_01 at (12.3, 8.7) with confidence 0.80
Updated miner_id : miner_02 at (15.1, 22.4) with confidence 0.80
...
```

**✅ Success Indicators:**
- You see "Listening for UDP messages on 0.0.0.0:5000"
- You see "Updated miner_id" messages appearing every 5 seconds
- A new file `mine_nav.db` appears in the `gateway/rpi-scripts` directory

**⚠️ Common Issues:**

| Issue | Solution |
|-------|----------|
| "Address already in use" | Another process is using port 5000. Find and stop it, or change the port in both simulator and gateway. |
| "IoT Client not initiated" | This is normal if you haven't configured Azure yet. Data still logs to SQLite. |
| No "Updated miner_id" messages | Check that the simulator is sending to the correct IP (Step 4). |

---

### Step 6: Install Dashboard Dependencies

Open another **new terminal window**:

```bash
# Navigate to the visualization directory
cd gateway/visualization

# Install dashboard dependencies
pip install -r requirements.txt
```

**Expected Output:**
```
Successfully installed dash-2.14.2 plotly-5.18.0 pandas-2.1.4
```

---

### Step 7: Launch the Visualization Dashboard

In the same terminal:

```bash
python dashboard.py
```

**Expected Output:**
```
============================================================
Mine Disaster Response - Visualization Dashboard
============================================================
Database path: ../rpi-scripts/mine_nav.db
Dashboard URL: http://localhost:8050

Visualization includes:
  - 12 BLE Beacons (diamond markers)
  - 35 Wall obstacles (thick gray lines)
  - Safe zone at (0, 15)

Make sure you have:
  1. main_v2.py running (creates the database)
  2. simulator running (generates miner data)
============================================================
 * Serving Flask app 'dashboard'
 * Debug mode: on
WARNING: This is a development server. Do not use it in production.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8050
 * Running on http://192.168.1.XXX:8050
```

---

### Step 8: View the Live Dashboard

Open your web browser and navigate to:

```
http://localhost:8050
```

**What You Should See:**

![Dashboard Overview](docs/images/dashboard-overview.png) *(conceptual - you can add a screenshot later)*

- 🟡 **12 orange diamond markers** - BLE beacons positioned throughout the mine
- ⬛ **Gray lines** - Mine walls creating a navigable maze
- 🔴🔵🟢 **Colored circles with labels (M1, M2, etc.)** - Live miner positions
- 🟢⭐ **Green star** - Safe zone at coordinates (0, 15)
- 📊 **Top metrics** - Number of miners tracked, average confidence, total updates
- 🔄 **Auto-refresh** - Updates every 2 seconds

**Interactive Features:**
- **Hover** over miners to see detailed position and confidence
- **Zoom** using scroll wheel or pinch gesture
- **Pan** by clicking and dragging
- **Toggle** between "Simulator Position" and "Estimated Position" modes

---

### Step 9: Verify the Complete Data Flow

You now have 4 terminal windows running:

1. **Simulator** - Generating miner movement and BLE data
2. **Gateway** - Processing data and logging to SQLite
3. **Dashboard** - Visualizing live positions
4. *(Your original terminal for running commands)*

**Verification Checklist:**

✅ **Simulator Output:**
```
Sent miner_01: pos(12.3, 8.7) with 8 BLE readings
Sent miner_02: pos(15.1, 22.4) with 7 BLE readings
Completed transmission at 19:35:42
```

✅ **Gateway Output:**
```
Updated miner_id : miner_01 at (12.3, 8.7) with confidence 0.80
Updated miner_id : miner_02 at (15.1, 22.4) with confidence 0.80
```

✅ **Dashboard:**
- Miners appear on the grid
- Positions update every 2 seconds
- Path traces show movement history
- Metrics show "5" miners tracked

✅ **Database:**
```bash
# In a new terminal, check the database
cd gateway/rpi-scripts
sqlite3 mine_nav.db "SELECT COUNT(*) FROM miner_telemetry;"
# Should show increasing count (e.g., 150, 200, 250...)
```

---

## ⏸️ Stopping the System

When you're done testing:

1. **Stop the Dashboard:** Press `Ctrl+C` in the dashboard terminal
2. **Stop the Gateway:** Press `Ctrl+C` in the gateway terminal
3. **Stop the Simulator:** Press `Ctrl+C` in the simulator terminal (or run `docker-compose down`)

The database file (`mine_nav.db`) will persist, so your data is saved for later analysis.

---

## 🌐 Full System Setup (With Azure Integration)

**Time Estimate:** 30-45 minutes (first time) | 10 minutes (subsequent deploys)

This section covers deploying the cloud infrastructure and connecting your gateway to Azure.

### Prerequisites for Azure Deployment

- Active Azure subscription
- Azure CLI installed and logged in
- Terraform installed

### Step 1: Azure CLI Login

```bash
az login
```

This will open a browser window for authentication.

**Expected Output:**
```json
[
  {
    "cloudName": "AzureCloud",
    "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "isDefault": true,
    "name": "Your Subscription Name",
    "state": "Enabled"
  }
]
```

---

### Step 2: Deploy Azure Infrastructure with Terraform

```bash
# Navigate to the Terraform directory
cd cloud/terraform

# Initialize Terraform
terraform init
```

**Expected Output:**
```
Initializing the backend...
Initializing provider plugins...
Terraform has been successfully initialized!
```

**Configure Your Deployment:**

Edit `terraform.tfvars`:

```hcl
# Your unique resource naming prefix
resource_prefix = "mine-resp"  # Change this to something unique

# Azure region
location = "eastus"

# IoT Hub settings
iot_hub_sku = "S1"  # Use "F1" for free tier (limited features)
```

**Deploy the Infrastructure:**

```bash
# Preview what will be created
terraform plan

# Apply the configuration
terraform apply
```

Type `yes` when prompted.

**Expected Output:**
```
Apply complete! Resources: 7 added, 0 changed, 0 destroyed.

Outputs:

cosmosdb_endpoint = "https://mine-resp-cosmos.documents.azure.com:443/"
iot_hub_hostname = "mine-resp-iothub.azure-devices.net"
iot_hub_device_connection_string = "HostName=mine-resp-iothub.azure-devices.net;DeviceId=rpi-gateway;SharedAccessKey=..."
```

**⚠️ IMPORTANT:** Copy the `iot_hub_device_connection_string` output. You'll need it in the next step.

**Troubleshooting:**
- "Resource name already exists" - Change `resource_prefix` in `terraform.tfvars`
- "Quota exceeded" - You may have hit Azure limits; try a different region or subscription
- For detailed Terraform help, see [`/cloud/terraform/README.md`](./cloud/terraform/README.md)

---

### Step 3: Configure the Gateway for Azure

Set the IoT Hub connection string as an environment variable:

**On Windows:**
```bash
set IOTHUB_DEVICE_CONNECTION_STRING="HostName=mine-resp-iothub.azure-devices.net;DeviceId=rpi-gateway;SharedAccessKey=..."
```

**On Mac/Linux:**
```bash
export IOTHUB_DEVICE_CONNECTION_STRING="HostName=mine-resp-iothub.azure-devices.net;DeviceId=rpi-gateway;SharedAccessKey=..."
```

**To make it permanent**, add the export command to `~/.bashrc` (Linux) or `~/.zshrc` (Mac).

---

### Step 4: Restart the Gateway with Azure Connection

```bash
cd gateway/rpi-scripts
python main_v2.py
```

**Expected Output (with Azure):**
```
Starting BLE Fingerprinting Gateway...
IoT Hub Client connected  # ✅ This line means Azure is working!
Starting UDP Listener...
Listening for UDP messages on 0.0.0.0:5000
Message sent to Azure: {'device_id': 'miner_01', 'timestamp': '2025-11-15T19:35:42', ...}
```

**✅ Success:** You should now see "Message sent to Azure" instead of "Skipping message"!

---

### Step 5: Verify Data in Azure Cosmos DB

**Option 1: Azure Portal**
1. Go to [portal.azure.com](https://portal.azure.com)
2. Navigate to your Cosmos DB account (e.g., `mine-resp-cosmos`)
3. Go to Data Explorer
4. Expand `mine-telemetry-db` → `miner-positions`
5. Click "Items" - you should see JSON documents for each miner

**Option 2: Azure CLI**
```bash
# List documents (requires Azure Cosmos DB CLI extension)
az cosmosdb sql container query \
  --account-name mine-resp-cosmos \
  --database-name mine-telemetry-db \
  --container-name miner-positions \
  --query-text "SELECT * FROM c ORDER BY c._ts DESC OFFSET 0 LIMIT 10"
```

**What You Should See:**
```json
{
  "device_id": "miner_01",
  "timestamp": "2025-11-15T19:35:42.123456",
  "position": {
    "x": 12.3,
    "y": 8.7
  },
  "confidence": 0.8,
  "ble_readings": {
    "beacon_001": -65.2,
    "beacon_002": -72.8,
    ...
  }
}
```

---

## 📊 System Architecture Overview

Now that everything is running, here's what you've built:

```
┌─────────────────┐
│  Simulator      │  Generates BLE data
│ (Docker)        │  UDP packets every 5s
└────────┬────────┘
         │ UDP :5000
         ▼
┌─────────────────┐
│  RPi Gateway    │  Processes & stores
│ (main_v2.py)    │  locally + Azure
└───┬─────────┬───┘
    │         │
    │         └──────────────┐
    │                        │ MQTT/AMQP
    │ SQLite writes          ▼
    ▼                 ┌─────────────────┐
┌─────────────────┐  │  Azure IoT Hub  │
│  mine_nav.db    │  └────────┬────────┘
│  (SQLite)       │           │
└────────┬────────┘           │ Stream Analytics
         │ reads              ▼
         │            ┌─────────────────┐
         │            │  Cosmos DB      │
         │            │  (Cloud Store)  │
         │            └─────────────────┘
         ▼
┌─────────────────┐
│  Dashboard      │  Live visualization
│ (dashboard.py)  │  http://localhost:8050
└─────────────────┘
```

---

## �� Testing & Verification

### Test 1: Miner Movement

Watch the dashboard for 30 seconds. You should see:
- Miners moving smoothly across the grid
- Path traces extending behind them
- Positions updating every 2 seconds

### Test 2: BLE Beacon Detection

In the gateway terminal, you should see varying numbers of BLE readings per miner:

```
Updated miner_id : miner_01 at (5.2, 5.1) with confidence 0.80  # Near beacon_001
Updated miner_id : miner_02 at (25.3, 25.8) with confidence 0.80  # Near beacon_009
```

Miners closer to beacons will detect more beacons with stronger signals.

### Test 3: Database Integrity

```bash
cd gateway/rpi-scripts
sqlite3 mine_nav.db

# Check record count
SELECT COUNT(*) FROM miner_telemetry;

# Check latest positions
SELECT device_id, estimated_x, estimated_y, confidence, timestamp 
FROM miner_telemetry 
ORDER BY timestamp DESC 
LIMIT 10;

# Exit SQLite
.quit
```

### Test 4: Azure Data Flow (if configured)

Check the gateway terminal for:
```
Message sent to Azure: {'device_id': 'miner_01', ...}
```

Then verify in Azure Portal → Cosmos DB → Data Explorer.

---

## ⚠️ Troubleshooting Guide

### Common Issues and Solutions

#### "Database is locked"

**Problem:** SQLite can't handle simultaneous reads/writes
**Solution:** 
- Stop the dashboard
- Wait 5 seconds
- Restart the dashboard
- If persistent, add this to `dashboard.py` line 87:
  ```python
  conn = sqlite3.connect(DB_PATH, timeout=10.0)
  ```

---

#### Simulator not sending data

**Problem:** Network configuration issue
**Solutions:**
1. Verify the `HOST` in `init_simulator_v2.py` matches your machine's IP
2. Check firewall settings (may need to allow port 5000)
3. On Windows, try `127.0.0.1` instead of your local IP

---

#### Dashboard shows "Waiting for data..."

**Problem:** No data in the database
**Checklist:**
- [ ] Is the simulator running? (`docker ps` should show the container)
- [ ] Is the gateway running? (Check for "Listening on 0.0.0.0:5000")
- [ ] Does `mine_nav.db` exist? (Should be in `gateway/rpi-scripts/`)
- [ ] Does the database have records? (Run the SQLite query from Test 3)

---

#### Azure connection fails

**Problem:** Invalid connection string or network issue
**Solutions:**
1. Verify the connection string has no extra spaces or newlines
2. Check if your network blocks outbound MQTT/AMQP (ports 8883, 5671)
3. Try the test script:
   ```bash
   cd gateway/rpi-scripts
   python test_azure.py
   ```
4. Regenerate the connection string in Azure Portal if needed

---

#### Docker container exits immediately

**Problem:** Python script has an error
**Solution:**
```bash
# View container logs
docker-compose logs

# Run in foreground to see errors
docker-compose up
```

---

## 📚 Next Steps

Now that you have the system running:

### For Developers

1. **Implement ML Position Estimation**
   - See [`/algorithms/README.md`](./algorithms/README.md)
   - Train a k-NN model on BLE fingerprints
   - Replace the stub in `estimate_miner_position()` in `main_v2.py`

2. **Add A* Pathfinding**
   - Implement the `a_star_pathfinding()` function in `main_v2.py`
   - Use the `WALLS` definition from `dashboard.py` as obstacles

3. **Enhance the Dashboard**
   - Add alerts for low battery miners
   - Show computed navigation paths
   - Add historical playback feature

### For Hardware Team

1. **Flash ESP32 Firmware**
   - See [`/hardware/esp32-firmware/README.md`](./hardware/esp32-firmware/README.md)
   - Replace simulator with real hardware devices

2. **Set Up Physical BLE Beacons**
   - Position beacons according to the coordinates in `BLE_BEACONS`
   - Calibrate transmission power for optimal RSSI readings

### For Cloud Team

1. **Add Stream Analytics Job**
   - Set up real-time aggregations
   - Configure alerts for anomalies

2. **Set Up Monitoring**
   - Add Application Insights
   - Configure Azure Monitor alerts

---

## 📖 Additional Resources

### Documentation
- [System Contracts (Data Schemas)](./docs/contracts.md) - **Read this first!**
- [Terraform Infrastructure Guide](./cloud/terraform/README.md)
- [Gateway Implementation Details](./gateway/rpi-scripts/README.md)
- [Simulator Documentation](./gateway/docker-simulator/README.md)
- [Dashboard Architecture](./gateway/visualization/ARCHITECTURE.md)
- [ML Algorithms Guide](./algorithms/README.md)

### Helpful Commands

```bash
# Check if ports are in use
netstat -an | grep 5000  # Gateway port
netstat -an | grep 8050  # Dashboard port

# View Docker logs
docker-compose logs -f

# Clean up Docker
docker-compose down --volumes  # Remove containers and volumes

# Reset the database
rm gateway/rpi-scripts/mine_nav.db  # Then restart gateway

# Azure resource cleanup (careful! this deletes everything)
cd cloud/terraform
terraform destroy
```

---

## 🆘 Getting Help

If you're stuck:

1. **Check the specific component's README** - Each directory has detailed docs
2. **Review the troubleshooting section** above
3. **Check the GitHub Issues** - Someone may have faced the same problem
4. **Open a new issue** - Provide logs and steps to reproduce

---

## ✅ Completion Checklist

You've successfully set up the system when you can check all these boxes:

**Local Setup:**
- [ ] Simulator is running and sending UDP packets
- [ ] Gateway is receiving data and logging to SQLite
- [ ] Dashboard shows live miner positions
- [ ] All 12 BLE beacons are visible on the dashboard
- [ ] Mine maze walls are displayed correctly
- [ ] Miners are moving and leaving path traces

**Azure Setup (Optional):**
- [ ] Terraform deployed all resources successfully
- [ ] Gateway shows "IoT Hub Client connected"
- [ ] Messages are appearing in Cosmos DB
- [ ] No error messages in any terminal

---

## 🎓 Learning Path

**For Complete Beginners:**
1. Start with the local setup (no Azure)
2. Understand how the simulator generates data
3. Explore the SQLite database structure
4. Modify the dashboard to add your own visualizations
5. Then move to Azure deployment

**For Experienced Developers:**
1. Skim the architecture diagram
2. Jump straight to full Azure setup
3. Focus on implementing the ML position estimation
4. Contribute to the pathfinding algorithms

---

## 📝 Changelog

**v2.0 (2025-11-15)**
- Added BLE fingerprinting simulation
- Introduced live visualization dashboard
- Updated to use SQLite + Azure Cosmos DB
- Added maze layout for pathfinding

**v1.0 (Previous)**
- Initial trilateration-based implementation
- Basic Azure IoT Hub integration

---

**🎉 Congratulations!** You now have a fully functional Mine Disaster Response system running. Happy coding, and stay safe! 🦺

---

*For questions or contributions, please open an issue on GitHub or contact the team leads listed in the main [README.md](./README.md).*
