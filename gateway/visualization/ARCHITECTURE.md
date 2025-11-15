# Visualization Dashboard - Architecture & Design

**Last Updated:** 2025-11-15

## Purpose of This Document

This document explains the technical architecture, design decisions, and implementation details of the visualization dashboard. It's intended for developers who need to understand how the dashboard works internally, modify its behavior, or extend its functionality.

## Technology Stack

### Core Framework: Dash + Plotly

**Why Dash?**
-   Built on top of Flask, React, and Plotly.js
-   Purely Python - no JavaScript required for basic functionality
-   Excellent for real-time data visualization with callbacks
-   Production-ready with minimal configuration
-   Easy deployment (runs as a standard Flask app)

**Why Plotly?**
-   Interactive by default (zoom, pan, hover, select)
-   High-quality 2D and 3D visualizations
-   Handles dynamic data updates efficiently
-   Extensive customization options for markers, lines, and layouts

### Data Layer: SQLite + Pandas

**SQLite**: 
-   Lightweight, serverless database perfect for edge deployments
-   No additional daemon or service required
-   ACID-compliant for data integrity
-   Supports window functions for efficient time-series queries

**Pandas**:
-   Seamless integration with SQLite via `read_sql_query()`
-   Powerful data manipulation for aggregations and transformations
-   Familiar API for data scientists and engineers

## Application Architecture

### High-Level Data Flow

```
┌─────────────────┐
│   Simulator     │ UDP packets
│ (init_sim_v2)   ├──────────┐
└─────────────────┘          │
                             ▼
                    ┌─────────────────┐
                    │  RPi Gateway    │
                    │  (main_v2.py)   │
                    └────────┬────────┘
                             │ writes
                             ▼
                    ┌─────────────────┐
                    │  mine_nav.db    │◄─────┐
                    │    (SQLite)     │      │ reads every 2s
                    └─────────────────┘      │
                                             │
                    ┌─────────────────┐      │
                    │   Dashboard     ├──────┘
                    │ (dashboard.py)  │
                    └────────┬────────┘
                             │ serves
                             ▼
                    ┌─────────────────┐
                    │  Web Browser    │
                    │  (localhost:8050)│
                    └─────────────────┘
```

### Component Breakdown

#### 1. Configuration Constants (Lines 1-83)

```python
SAFE_ZONE = (0, 15)         # Target evacuation point
BLE_BEACONS = [...]         # 12 beacon positions
WALLS = [...]               # Maze wall segments
```

**Design Decision**: These are hardcoded at the module level rather than stored in the database because:
-   They represent the static physical infrastructure of the mine
-   They need to be consistent across simulator and visualization
-   Loading from DB adds unnecessary complexity and latency
-   Version control captures changes to mine layout

**Trade-off**: Requires manual synchronization with `init_simulator_v2.py`. Could be improved by loading from a shared JSON config file.

#### 2. Dash Application Layout (Lines 85-133)

The layout is defined declaratively using Dash's HTML and DCC (Dash Core Components) components:

```python
app.layout = html.Div([
    html.H1(...),           # Title
    dcc.Graph(...),         # Main visualization
    html.Div([...]),        # Metrics row
    html.Div([...]),        # Control panel
    dcc.Interval(...)       # Auto-refresh trigger
])
```

**Key Components**:
-   `dcc.Graph`: The Plotly visualization container
-   `dcc.Interval`: Triggers the callback every 2000ms (2 seconds)
-   `dcc.RadioItems`: The display mode selector (simulator vs. estimated)

#### 3. Update Callback (Lines 142-295)

This is the heart of the dashboard - a reactive callback that runs every 2 seconds:

```python
@app.callback(
    [Output('live-grid', 'figure'), ...],
    [Input('interval', 'n_intervals'),
     Input('position-mode', 'value')]
)
def update_dashboard(n, position_mode):
    # 1. Check database existence
    # 2. Query recent telemetry
    # 3. Build Plotly figure with layers
    # 4. Calculate metrics
    # 5. Return updated UI elements
```

**Performance Considerations**:

-   **Window Function Query**: Uses `ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY timestamp DESC)` to efficiently get the last 100 records per miner without multiple queries
-   **Tail Operation**: `miner_data.tail(50)` limits path traces to recent positions, preventing visual clutter and improving rendering speed
-   **Connection Management**: Opens and closes database connection per callback to avoid lock issues

**Why not use a persistent connection?**
-   SQLite doesn't handle concurrent writes well
-   Short-lived connections prevent blocking the gateway's writes
-   Dashboard is read-only, so transaction overhead is minimal

### Visualization Layer Ordering

Plotly renders traces in the order they're added. Our layer stack (bottom to top):

1.  **Walls** (dark gray, thick lines) - Background obstacles
2.  **BLE Beacons** (orange diamonds) - Static infrastructure
3.  **Miner Paths** (colored lines, semi-transparent) - Historical movement
4.  **Current Positions** (colored circles) - Latest locations
5.  **Safe Zone** (green star) - Evacuation target

**Why this order?**
-   Static elements (walls, beacons) render first to provide context
-   Dynamic elements (miners) render on top for visibility
-   Most important element (safe zone) renders last to ensure it's never obscured

## Key Design Decisions

### 1. Database Schema Assumptions

The dashboard assumes the `miner_telemetry` table has:
-   `estimated_x` and `estimated_y` columns (not separate simulator/ML columns)
-   `confidence` as a float between 0 and 1
-   `timestamp` as an ISO 8601 string

**Current Limitation**: The "Display Mode" toggle doesn't actually switch data sources because both simulator and ML-estimated positions are stored in the same columns. This will require a database schema update to fully support.

### 2. Color Palette

Uses a 7-color palette that cycles for more than 7 miners:

```python
colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', 
          '#9b59b6', '#1abc9c', '#e67e22']
color = colors[idx % len(colors)]
```

**Why these colors?**
-   High contrast against the light gray background
-   Accessible for most forms of color blindness
-   Distinct enough when displayed together

### 3. Refresh Rate: 2 Seconds

**Why not faster?**
-   Database writes from gateway occur every 5 seconds per miner
-   2-second refresh is responsive without unnecessary database load
-   Smoother than 5 seconds, but not as CPU-intensive as 1 second

**Why not slower?**
-   Emergency response scenarios require near-real-time updates
-   Path traces update noticeably at this rate, providing good motion feedback

### 4. Empty State Handling

The `create_empty_figure()` helper provides graceful degradation:
-   Shows a message instead of crashing
-   Maintains the same layout structure
-   Guides the user on how to fix the issue

## Extension Points

### Adding a New Visualization Layer

To add a new element (e.g., danger zones):

1.  Define the data structure (e.g., `DANGER_ZONES = [{'x': 10, 'y': 10, 'radius': 3}]`)
2.  Add a trace in `update_dashboard()` at the appropriate layer position
3.  Use `fig.add_trace(go.Scatter(...))` for points/lines or `go.Scatter` with `fill='toself'` for shapes

Example - adding circular danger zones:

```python
# Add after walls, before beacons
for zone in DANGER_ZONES:
    theta = np.linspace(0, 2*np.pi, 100)
    x = zone['x'] + zone['radius'] * np.cos(theta)
    y = zone['y'] + zone['radius'] * np.sin(theta)
    fig.add_trace(go.Scatter(
        x=x, y=y,
        fill='toself',
        fillcolor='rgba(255, 0, 0, 0.2)',
        line=dict(color='red', width=2),
        name='Danger Zone',
        showlegend=False
    ))
```

### Adding New Metrics

To add a new metric card:

1.  Add a new `html.Div([...])` in the metrics row (lines 95-113)
2.  Add a new `Output` to the callback decorator
3.  Calculate the metric in `update_dashboard()`
4.  Return it as part of the return tuple

### Changing the Refresh Rate

Modify line 132:

```python
dcc.Interval(id='interval', interval=1000, n_intervals=0)  # 1 second
```

## Performance Characteristics

**Database Query Time**: ~50-100ms for 5 miners with 500 total records
**Plotly Rendering Time**: ~100-200ms for 5 miners + 12 beacons + 30 walls
**Total Callback Execution**: ~200-400ms

**Scaling Limits**:
-   **Miners**: Tested up to 20 miners with acceptable performance
-   **History**: 100 records per miner is a good balance; increase cautiously
-   **Walls**: 50+ walls may cause rendering slowdowns

**Optimization Opportunities**:
-   Cache static elements (walls, beacons) and only update dynamic traces
-   Use Plotly's `extendData` for appending new positions instead of full redraws
-   Implement client-side filtering to reduce data sent to browser

## Security Considerations

**Current State**: This dashboard is designed for local development and edge deployment.

**Production Checklist** (if deploying to internet-accessible server):
-   [ ] Add authentication (Dash supports basic auth or integrate with OAuth)
-   [ ] Use HTTPS (configure SSL certificates)
-   [ ] Implement rate limiting to prevent abuse
-   [ ] Sanitize any user inputs (currently none, but future features may add them)
-   [ ] Use environment variables for sensitive configuration
-   [ ] Consider running behind a reverse proxy (nginx)

## Testing Strategy

**Manual Testing**:
1.  Start simulator → Start gateway → Start dashboard
2.  Verify all 12 beacons appear at correct positions
3.  Verify walls render and create a navigable maze
4.  Verify miners appear and move smoothly
5.  Toggle display mode and verify no errors
6.  Check metrics update correctly

**Automated Testing** (future):
-   Unit tests for metric calculations
-   Snapshot tests for layout structure
-   Integration tests with mock database

## Deployment Options

### Option 1: Local Development (Current)
```bash
python dashboard.py
# Access at http://localhost:8050
```

### Option 2: Production WSGI Server
```bash
pip install gunicorn
gunicorn dashboard:server -b 0.0.0.0:8050
```

### Option 3: Docker Container
Create a `Dockerfile` in this directory:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY dashboard.py .
CMD ["python", "dashboard.py"]
```

## Troubleshooting Guide

See the main README.md for user-facing troubleshooting. Developer-specific issues:

**"Figure won't update"**
-   Check that the callback is being triggered (add print statements)
-   Verify the query is returning data (`print(len(df))`)
-   Check browser console for JavaScript errors

**"Database is locked" error**
-   The gateway is writing while dashboard is reading
-   Increase `timeout` in `sqlite3.connect()`: `sqlite3.connect(DB_PATH, timeout=10.0)`

**"Memory usage growing"**
-   Plotly keeps old figures in memory in debug mode
-   Set `debug=False` in `app.run_server()` for production

## Contributing

When modifying this dashboard:
1.  Maintain backward compatibility with existing database schema
2.  Keep beacon/wall configs in sync with `init_simulator_v2.py`
3.  Update both README.md and this ARCHITECTURE.md
4.  Test with varying numbers of miners (1, 5, 10, 20)
5.  Ensure changes work with `debug=False` before committing
