import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import sqlite3
import pandas as pd
from datetime import datetime
import os
import json

app = dash.Dash(__name__)

# CRITICAL: Path to your actual database location
# This assumes you run the dashboard from gateway/visualization/
DB_PATH = os.path.join(os.path.dirname(__file__), '../rpi-scripts/mine_nav.db')

# Safe zone configuration (matches your main_v2.py)
SAFE_ZONE = (0, 15)

# BLE Beacon positions (matches init_simulator_v2.py exactly)
BLE_BEACONS = [
    {'id': 'beacon_001', 'x': 5, 'y': 5},
    {'id': 'beacon_002', 'x': 5, 'y': 15},
    {'id': 'beacon_003', 'x': 5, 'y': 25},
    {'id': 'beacon_004', 'x': 15, 'y': 5},
    {'id': 'beacon_005', 'x': 15, 'y': 15},
    {'id': 'beacon_006', 'x': 15, 'y': 25},
    {'id': 'beacon_007', 'x': 25, 'y': 5},
    {'id': 'beacon_008', 'x': 25, 'y': 15},
    {'id': 'beacon_009', 'x': 25, 'y': 25},
    {'id': 'beacon_010', 'x': 10, 'y': 10},
    {'id': 'beacon_011', 'x': 20, 'y': 20},
    {'id': 'beacon_012', 'x': 10, 'y': 20},
]

# Wall definitions - Maze layout for mine tunnels
# Each wall is defined as [(x1, y1), (x2, y2)]
WALLS = [
    # Main vertical corridors (with gaps for horizontal movement)
    [(5, 0), (5, 8)],        # Left vertical - bottom section
    [(5, 12), (5, 20)],      # Left vertical - top section (gap at 8-12)
    
    [(10, 5), (10, 15)],     # Left-center vertical (gap at bottom and top)
    [(10, 18), (10, 25)],    # Left-center vertical - upper section
    
    [(15, 0), (15, 10)],     # Center vertical - bottom section
    [(15, 13), (15, 22)],    # Center vertical - upper section (gap at 10-13)
    
    [(20, 8), (20, 18)],     # Right-center vertical (gaps at top and bottom)
    [(20, 22), (20, 30)],    # Right-center vertical - top section
    
    [(25, 0), (25, 12)],     # Right vertical - bottom section
    [(25, 16), (25, 25)],    # Right vertical - upper section (gap at 12-16)
    
    # Main horizontal corridors (with gaps for vertical movement)
    [(0, 5), (8, 5)],        # Bottom horizontal - left section
    [(12, 5), (20, 5)],      # Bottom horizontal - right section (gap at 8-12)
    
    [(5, 10), (13, 10)],     # Lower-center horizontal - left section
    [(17, 10), (28, 10)],    # Lower-center horizontal - right section (gap at 13-17)
    
    [(0, 15), (8, 15)],      # Center horizontal - left section (safe zone accessible!)
    [(12, 15), (18, 15)],    # Center horizontal - middle section
    [(22, 15), (30, 15)],    # Center horizontal - right section (gaps at 8-12 and 18-22)
    
    [(8, 20), (18, 20)],     # Upper-center horizontal (gaps at sides)
    [(22, 20), (28, 20)],    # Upper-center horizontal - right section
    
    [(0, 25), (10, 25)],     # Top horizontal - left section
    [(14, 25), (22, 25)],    # Top horizontal - right section (gap at 10-14)
    
    # Internal maze walls - creating interesting paths
    [(7, 2), (13, 2)],       # Bottom internal horizontal
    [(17, 7), (23, 7)],      # Lower-right horizontal
    [(3, 12), (8, 12)],      # Left-side horizontal
    [(12, 17), (17, 17)],    # Mid-upper horizontal
    [(22, 22), (27, 22)],    # Top-right horizontal
    
    # Vertical maze elements
    [(8, 15), (8, 18)],      # Small vertical connector
    [(18, 0), (18, 6)],      # Bottom vertical
    [(23, 12), (23, 18)],    # Right-side vertical
    [(13, 27), (13, 30)],    # Upper vertical
    [(27, 3), (27, 8)],      # Bottom-right vertical
]

app.layout = html.Div([
    html.H1("Mine Disaster Response - Live Demo", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    # Main grid visualization
    dcc.Graph(id='live-grid', style={'height': '700px'}),
    
    # Metrics row
    html.Div([
        html.Div([
            html.H3("Miners Tracked", style={'color': '#2c3e50', 'margin': '0'}),
            html.H2(id='miners-tracked', style={'color': '#3498db', 'margin': '10px 0'})
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#ecf0f1', 'margin': '10px', 'borderRadius': '10px', 'flex': '1'}),
        
        html.Div([
            html.H3("Avg Confidence", style={'color': '#2c3e50', 'margin': '0'}),
            html.H2(id='avg-confidence', style={'color': '#27ae60', 'margin': '10px 0'})
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#ecf0f1', 'margin': '10px', 'borderRadius': '10px', 'flex': '1'}),
        
        html.Div([
            html.H3("Total Updates", style={'color': '#2c3e50', 'margin': '0'}),
            html.H2(id='total-updates', style={'color': '#e74c3c', 'margin': '10px 0'})
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#ecf0f1', 'margin': '10px', 'borderRadius': '10px', 'flex': '1'}),
    ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '20px'}),
    
    # Control panel
    html.Div([
        html.Label("Display Mode:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.RadioItems(
            id='position-mode',
            options=[
                {'label': ' Simulator Position (Ground Truth)', 'value': 'simulator'},
                {'label': ' Estimated Position (ML Model)', 'value': 'estimated'}
            ],
            value='simulator',
            inline=True,
            style={'fontSize': '16px'}
        )
    ], style={'textAlign': 'center', 'marginBottom': '20px', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '10px'}),
    
    # Auto-refresh every 2 seconds
    dcc.Interval(id='interval', interval=2000, n_intervals=0)
], style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'backgroundColor': '#ffffff'})

def parse_position_from_blob(ble_readings_json):
    """Extract simulator position from BLE readings blob if it exists"""
    try:
        data = json.loads(ble_readings_json)
        # The simulator embeds position in the message, check if we stored it
        return None  # Not stored in BLE readings
    except:
        return None

@app.callback(
    [Output('live-grid', 'figure'),
     Output('miners-tracked', 'children'),
     Output('avg-confidence', 'children'),
     Output('total-updates', 'children')],
    [Input('interval', 'n_intervals'),
     Input('position-mode', 'value')]
)
def update_dashboard(n, position_mode):
    # Check if database exists
    if not os.path.exists(DB_PATH):
        empty_fig = create_empty_figure("Waiting for database... Make sure main_v2.py is running.")
        return empty_fig, "0", "N/A", "0"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Query to get recent telemetry
        # We'll get the last 100 records per miner for path traces
        query = """
            WITH RankedData AS (
                SELECT 
                    device_id, 
                    timestamp, 
                    ble_readings,
                    estimated_x, 
                    estimated_y, 
                    confidence,
                    ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY timestamp DESC) as rn
                FROM miner_telemetry
                WHERE device_id LIKE 'miner_%'
            )
            SELECT device_id, timestamp, ble_readings, estimated_x, estimated_y, confidence
            FROM RankedData
            WHERE rn <= 100
            ORDER BY device_id, timestamp
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            empty_fig = create_empty_figure("Waiting for miner data... Make sure the simulator is running.")
            return empty_fig, "0", "N/A", "0"
        
    except Exception as e:
        print(f"Database error: {e}")
        empty_fig = create_empty_figure(f"Database error: {str(e)}")
        return empty_fig, "Error", "Error", "Error"
    
    # Create figure
    fig = go.Figure()
    
    # *** ADD WALLS FIRST (so they appear in background) ***
    for idx, wall in enumerate(WALLS):
        fig.add_trace(go.Scatter(
            x=[wall[0][0], wall[1][0]],
            y=[wall[0][1], wall[1][1]],
            mode='lines',
            name='Walls' if idx == 0 else None,
            line=dict(color='#34495e', width=8),
            showlegend=(idx == 0),
            legendgroup='walls',
            hovertemplate='<b>Wall Obstacle</b><extra></extra>'
        ))
    
    # *** ADD BLE BEACONS ***
    beacon_x = [b['x'] for b in BLE_BEACONS]
    beacon_y = [b['y'] for b in BLE_BEACONS]
    beacon_text = [b['id'].replace('beacon_', 'B') for b in BLE_BEACONS]
    
    fig.add_trace(go.Scatter(
        x=beacon_x,
        y=beacon_y,
        mode='markers+text',
        name='BLE Beacons',
        marker=dict(
            size=15,
            color='#f39c12',
            symbol='diamond',
            line=dict(color='#d68910', width=2)
        ),
        text=beacon_text,
        textposition='top center',
        textfont=dict(size=9, color='#d68910', family='Arial'),
        hovertemplate='<b>%{text}</b><br>Position: (%{x}, %{y})<extra></extra>'
    ))
    
    # Color palette for miners
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22']
    
    for idx, miner_id in enumerate(df['device_id'].unique()):
        miner_data = df[df['device_id'] == miner_id].sort_values('timestamp')
        
        color = colors[idx % len(colors)]
        
        # Use the selected position mode
        x_col = 'estimated_x'
        y_col = 'estimated_y'
        
        # Path trace (last 50 points for clarity)
        trace_data = miner_data.tail(50)
        fig.add_trace(go.Scatter(
            x=trace_data[x_col],
            y=trace_data[y_col],
            mode='lines',
            name=f'{miner_id} path',
            line=dict(color=color, width=2),
            opacity=0.6,
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Current position (most recent point)
        current = miner_data.iloc[-1]
        fig.add_trace(go.Scatter(
            x=[current[x_col]],
            y=[current[y_col]],
            mode='markers+text',
            name=miner_id,
            marker=dict(size=20, color=color, symbol='circle', line=dict(color='white', width=3)),
            text=[miner_id.replace('miner_', 'M')],
            textposition='middle center',
            textfont=dict(size=10, color='white', family='Arial Black'),
            hovertemplate=f'<b>{miner_id}</b><br>X: %{{x:.1f}}<br>Y: %{{y:.1f}}<br>Confidence: {current["confidence"]:.2f}<extra></extra>'
        ))
    
    # Add safe zone marker
    fig.add_trace(go.Scatter(
        x=[SAFE_ZONE[0]],
        y=[SAFE_ZONE[1]],
        mode='markers+text',
        name='Safe Zone',
        marker=dict(size=50, color='green', symbol='star', line=dict(color='darkgreen', width=3)),
        text=['SAFE'],
        textposition='bottom center',
        textfont=dict(size=14, color='darkgreen', family='Arial Black'),
        hovertemplate='<b>Safe Zone</b><br>Target Location<extra></extra>'
    ))
    
    # Layout with grid
    fig.update_layout(
        xaxis=dict(
            range=[-1, 31],
            title='X Coordinate (meters)',
            showgrid=True,
            gridwidth=1,
            gridcolor='#e0e0e0',
            dtick=5,
            zeroline=True
        ),
        yaxis=dict(
            range=[-1, 31],
            title='Y Coordinate (meters)',
            showgrid=True,
            gridwidth=1,
            gridcolor='#e0e0e0',
            dtick=5,
            zeroline=True
        ),
        title=dict(
            text=f'Live Miner Positions (30×30 Grid) - {position_mode.capitalize()} Mode',
            x=0.5,
            xanchor='center'
        ),
        hovermode='closest',
        plot_bgcolor='#f5f5f5',
        paper_bgcolor='white',
        legend=dict(
            x=1.05,
            y=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#cccccc',
            borderwidth=1
        ),
        height=700
    )
    
    # Calculate metrics
    num_miners = df['device_id'].nunique()
    latest_per_miner = df.groupby('device_id').tail(1)
    avg_conf = latest_per_miner['confidence'].mean() * 100
    total_updates = len(df)
    
    return fig, str(num_miners), f"{avg_conf:.1f}%", str(total_updates)

def create_empty_figure(message):
    """Helper to create an empty figure with a message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=20, color='gray')
    )
    fig.update_layout(
        xaxis=dict(range=[0, 30], title='X Coordinate', showgrid=True),
        yaxis=dict(range=[0, 30], title='Y Coordinate', showgrid=True),
        title='Waiting for Data...',
        plot_bgcolor='#f5f5f5'
    )
    return fig

if __name__ == '__main__':
    print("="*60)
    print("Mine Disaster Response - Visualization Dashboard")
    print("="*60)
    print(f"Database path: {DB_PATH}")
    print(f"Dashboard URL: http://localhost:8050")
    print(f"\nVisualization includes:")
    print(f"  - {len(BLE_BEACONS)} BLE Beacons (diamond markers)")
    print(f"  - {len(WALLS)} Wall obstacles (thick gray lines)")
    print(f"  - Safe zone at {SAFE_ZONE}")
    print("\nMake sure you have:")
    print("  1. main_v2.py running (creates the database)")
    print("  2. simulator running (generates miner data)")
    print("="*60)
    app.run_server(debug=True, host='0.0.0.0', port=8050)
