# Visualization Dashboard - Real-time Miner Tracking

**Last Updated:** 2025-11-15
**Owner:** All Teams

## Overview

This directory contains the web-based visualization dashboard for the Mine Disaster Response system. Built with Dash and Plotly, it provides a real-time, interactive view of miner positions, BLE beacon locations, mine obstacles, and navigation paths within the 30×30 meter mine grid.

The dashboard reads telemetry data from the local SQLite database (`mine_nav.db`) populated by the RPi gateway and displays it in a clean, professional interface with live updates every 2 seconds.

## Features

-   **Real-time Miner Tracking**: Displays current positions and historical movement paths for all tracked miners
-   **BLE Beacon Visualization**: Shows all 12 BLE beacon positions as diamond markers, matching the simulator configuration
-   **Mine Maze Layout**: Renders wall obstacles to visualize the mine's tunnel structure and navigation constraints
-   **Safe Zone Indicator**: Highlights the target evacuation point with a star marker
-   **Dual Display Modes**: Toggle between simulator ground truth positions and ML-estimated positions
-   **Live Metrics**: Tracks number of miners, average position confidence, and total telemetry updates
-   **Interactive Controls**: Hover over elements for detailed information, zoom, pan, and filter the view
-   **Auto-refresh**: Updates every 2 seconds without manual intervention

## Setup and Usage

### Prerequisites

-   Python 3.7+
-   The RPi gateway (`main_v2.py`) must be running to populate the database
-   The simulator (`init_simulator_v2.py`) should be running to generate miner data

### Installation

1.  **Install Dependencies:**
    ```bash
    cd gateway/visualization
    pip install -r requirements.txt
    ```

2.  **Verify Database Path:**
    The dashboard expects the SQLite database at `../rpi-scripts/mine_nav.db`. If your setup differs, modify the `DB_PATH` constant in `dashboard.py`.

### Running the Dashboard

Execute the main script from this directory:

```bash
python dashboard.py
```

The dashboard will start on `http://localhost:8050`. Open this URL in your web browser to view the live visualization.

### Access from Other Devices

The dashboard binds to `0.0.0.0`, making it accessible from other devices on your network:

```
http://<your-rpi-ip>:8050
```

## How It Works

1.  **Data Source**: The dashboard reads from the `miner_telemetry` table in `mine_nav.db`, which is continuously updated by the RPi gateway.

2.  **Query Logic**: Every 2 seconds, it fetches the last 100 position records per miner using a SQL window function to efficiently retrieve recent data.

3.  **Visualization Layers** (rendered in this order):
    -   **Walls**: Thick gray lines representing mine obstacles and tunnel structure
    -   **BLE Beacons**: 12 diamond-shaped markers showing beacon positions from `init_simulator_v2.py`
    -   **Miner Paths**: Semi-transparent lines showing the last 50 positions for each miner
    -   **Current Positions**: Large colored circles with miner IDs
    -   **Safe Zone**: Green star marker at coordinates (0, 15)

4.  **Metrics Calculation**: Aggregates data to show:
    -   Number of unique miners tracked
    -   Average position estimation confidence
    -   Total telemetry records processed

## Configuration

### BLE Beacon Positions

The `BLE_BEACONS` list (lines 20-33) matches the exact beacon layout from `docker-simulator/init_simulator_v2.py`:

```python
BLE_BEACONS = [
    {'id': 'beacon_001', 'x': 5, 'y': 5},
    {'id': 'beacon_002', 'x': 5, 'y': 15},
    # ... 12 beacons total
]
```

**Important**: If you modify beacon positions in the simulator, update them here as well for visual consistency.

### Mine Maze Layout

The `WALLS` list (lines 36-83) defines the mine's tunnel structure as line segments. The current configuration creates a navigable maze with:
-   Multiple vertical and horizontal corridors
-   Strategic gaps allowing miner movement between sections
-   Dead ends and alternate paths for realistic pathfinding scenarios

To modify the maze:
1.  Edit the `WALLS` list, where each wall is defined as `[(x1, y1), (x2, y2)]`
2.  Ensure walls have gaps to allow navigation
3.  Keep coordinates within the 30×30 grid bounds

### Display Modes

The dashboard offers two position display modes:

-   **Simulator Position (Ground Truth)**: Shows the actual positions from the simulator (currently displayed as `estimated_x/y` in the database)
-   **Estimated Position (ML Model)**: Will show ML-predicted positions once the BLE fingerprinting model is integrated

*Note: Both modes currently show the same data until the ML position estimation in `main_v2.py` is fully implemented.*

## Database Schema

The dashboard queries the following table structure:

```sql
miner_telemetry (
    device_id TEXT,
    timestamp TEXT,
    ble_readings TEXT,      -- JSON of beacon RSSI values
    estimated_x REAL,
    estimated_y REAL,
    confidence REAL
)
```

## Troubleshooting

### "Waiting for database..." message

**Problem**: The dashboard can't find `mine_nav.db`

**Solutions**:
-   Ensure `main_v2.py` has been run at least once to create the database
-   Verify you're running the dashboard from `gateway/visualization/`
-   Check that the `DB_PATH` in line 15 points to the correct location

### "Waiting for miner data..." message

**Problem**: Database exists but has no miner records

**Solutions**:
-   Start the simulator: `docker-compose up` in `gateway/docker-simulator/`
-   Verify the simulator is sending to the correct gateway IP and port
-   Check that `main_v2.py` is running and receiving UDP packets

### Dashboard won't load or shows errors

**Problem**: Missing dependencies or port conflicts

**Solutions**:
-   Reinstall dependencies: `pip install -r requirements.txt`
-   Check if port 8050 is already in use: `lsof -i :8050` (Mac/Linux) or `netstat -ano | findstr :8050` (Windows)
-   Try a different port by modifying line 324: `app.run_server(debug=True, host='0.0.0.0', port=8051)`

### Walls or beacons not appearing

**Problem**: Visualization elements missing from the plot

**Solutions**:
-   Verify the `WALLS` and `BLE_BEACONS` lists are properly defined
-   Check browser console for JavaScript errors
-   Zoom out on the plot to ensure elements aren't outside the visible range

## Future Enhancements

-   **Pathfinding Visualization**: Display computed A* paths from miners to the safe zone
-   **Alert System**: Highlight miners with low battery or poor position confidence
-   **Historical Playback**: Scrub through time to replay miner movements
-   **Export Functionality**: Save visualization snapshots or export data to CSV
-   **Multi-level Mines**: Support for 3D visualization with different mine depths

## Integration with Other Components

This dashboard integrates with:

-   **`/gateway/rpi-scripts`**: Reads telemetry data from the SQLite database created by `main_v2.py`
-   **`/gateway/docker-simulator`**: Visualizes the beacon positions and mine layout defined in `init_simulator_v2.py`
-   **`/algorithms`**: Will display ML-predicted positions once the BLE fingerprinting model is integrated
-   **`/docs/contracts.md`**: Adheres to the telemetry data schema defined in the system contracts

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
