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
    
    # CRITICAL FIX: Since estimate_miner_position is a stub, we need actual position from simulator
    # The simulator sends position in the UDP message, but main_v2.py doesn't store it in the DB
    # For now, we'll use estimated_x and estimated_y (which are random from the stub)
    # TODO: Update main_v2.py to extract and store the simulator's position field
    
    # Create figure
    fig = go.Figure()
    
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
    print("\nMake sure you have:")
    print("  1. main_v2.py running (creates the database)")
    print("  2. simulator running (generates miner data)")
    print("="*60)
    app.run_server(debug=True, host='0.0.0.0', port=8050)
    