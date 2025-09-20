import json  # For JSON encoding/decoding
import sqlite3  # For SQLite database operations
import time  # For time-related functions
import socket  # For UDP socket operations
import threading  # For threading
from datetime import datetime  # For timestamping
from azure.iot.device import IoTHubDeviceClient, Message  # For Azure IoT Hub
import os  # For environment variables

# 1 - Configuration
# Azure IoT Hub Connection (uses environment variables set on the Pi)
CONNECTION_STRING = os.getenv('IOTHUB_DEVICE_CONNECTION_STRING')
# UDP Listener Configuration
UDP_IP = "0.0.0.0"  # Listen on all network interfaces
UDP_PORT = 5000  # Port to listen on
# Mine Configuration
MINE_GRID = [[1, 1, 1, 1, 1], [1, 0, 1, 0, 1], [1, 0, 0, 0, 1], 
            [1, 1, 0, 1, 1], [0, 1, 1, 0, 0]]  # 1=path, 0=wall
SAFE_ZONE = (3, 3)  # Coordinates of the safe zone in the mine grid
# In-memory storage for miner positions
current_miner_positions = {}
# Database connection lock to prevent concurrent access
db_lock = threading.Lock()
# IoT Hub client
iot_client = None

# 2 - Azure IoT Hub Setup
def init_iot_client():
    """Initialize and return an IoT Hub client."""
    try:
        client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
        client.connect()
        print("Connected to Azure IoT Hub.")
        return client
    except Exception as e:
        print(f"Failed to connect to Azure IoT Hub: {e}")
        return None

def send_to_azure(message_body):
    """Send a message to Azure IoT Hub."""
    global iot_client
    if not iot_client:
        print("IoT client not initialized. Skipping message.")
        return
        
    try:
        message = Message(json.dumps(message_body))
        iot_client.send_message(message)
        print(f"Sent to Azure: {message_body}")
    except Exception as e:
        print(f"Error sending to Azure: {e}")
        # Try to reconnect
        try:
            iot_client.disconnect()
            iot_client = init_iot_client()
        except:
            print("Failed to reconnect to Azure IoT Hub")

# 3 - SQLite Database Logging
def init_database():
    """Initialize the SQLite database to log all received data."""
    conn = sqlite3.connect('mine_nav.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS miner_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            timestamp TEXT,
            accel_x REAL,
            accel_y REAL,
            accel_z REAL,
            gyro_x REAL,
            gyro_y REAL,
            gyro_z REAL,
            rssi INTEGER,
            battery INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            timestamp TEXT,
            command TEXT,
            path TEXT 
        )
    ''')
    conn.commit()
    return conn

def log_miner_telemetry(conn, data):
    """Log miner telemetry data to the database."""
    with db_lock:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO miner_telemetry (device_id, timestamp, accel_x, accel_y, accel_z, 
                                        gyro_x, gyro_y, gyro_z, rssi, battery)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['device_id'], datetime.fromtimestamp(data['timestamp']).isoformat(), 
             data['accel_x'], data['accel_y'], data['accel_z'], data['gyro_x'], 
             data['gyro_y'], data['gyro_z'], data['rssi'], data['battery']))
        conn.commit()

def log_command(conn, miner_id, command, path):
    """Log command data to the database."""
    with db_lock:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO commands (device_id, timestamp, command, path)
            VALUES (?, ?, ?, ?)
        ''', (miner_id, datetime.now().isoformat(), command, json.dumps(path)))
        conn.commit()

# 4 - Pathfinding and Processing
def simulate_pathfinding(grid, miner_positions, goal):
    """STUB FUNCTION: Replace this with a real pathfinding algorithm."""
    paths = {}
    for miner_id, pos in miner_positions.items():
        # Simple Simulation : Moving towards a goal
        path = [pos, goal]
        paths[miner_id] = path
    return paths

def process_miner_data(data, db_conn):
    """Process incoming miner data."""
    global current_miner_positions
    # Log to database
    log_miner_telemetry(db_conn, data)
    # Update current position (for simulation, we use RSSI as a proxy for position)
    # In a real scenario, you'd have actual coordinates from a sensor fusion of IMU and LoRa data
    miner_id = data['device_id']
    if miner_id not in current_miner_positions:
        current_miner_positions[miner_id] = (0, 0)  # Start at origin for simulation
    else:
        x, y = current_miner_positions[miner_id]
        current_miner_positions[miner_id] = (min(x+1, 4), min(y+1, 4))  # Move diagonally for simulation
    # Print updated position
    print(f"Updated position for {miner_id}: {current_miner_positions[miner_id]}")
    # Check if in safe zone
    if current_miner_positions[miner_id] == SAFE_ZONE:
        print(f"{miner_id} has reached the safe zone!")

# 5 - UDP Listener
def udp_listener(db_conn):
    """Listen for incoming UDP packets from miners."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}")
    try:
        while True:
            data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
            try:
                message = json.loads(data.decode('utf-8'))
                print(f"Received message: {message} from {addr}")
                if 'fixed_x' in message:  # Simple check to differentiate miner data
                    pass  # Ignore anchor data for now
                elif 'accel_x' in message:  # Miner data
                    process_miner_data(message, db_conn)
                    send_to_azure(message)
                else:
                    print("Unknown message format")
            except json.JSONDecodeError:  # Handle invalid JSON
                print("Received invalid JSON")
    except KeyboardInterrupt:
        print("UDP listener stopped by user.")
    finally:
        sock.close()

# 6 - Main Loop
def main_loop(db_conn):
    """Main processing loop that runs periodically"""
    while True:
        try:
            # 1 - Run pathfinding if we have miner positions
            if current_miner_positions:
                paths = simulate_pathfinding(MINE_GRID, current_miner_positions, SAFE_ZONE)
                print(f"Calculated paths: {paths}")
                # Send commands to devices via LoRa (stubbed)
                # For now, just log the commands to the database
                for miner_id, path in paths.items():
                    log_command(db_conn, miner_id, 'move', path)
            else:
                print("No miner positions available for pathfinding.")
                
            # Send status update to Azure
            status_message = {
                "gateway_id": "rpi_mine_entrance", 
                "timestamp": datetime.now().isoformat(), 
                "status": "operational", 
                "miners_tracked": len(current_miner_positions), 
                "message": "Periodic status update"
            }
            send_to_azure(status_message)
            
            # Wait before next iteration
            time.sleep(30)  # Run every 30 seconds
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(10)  # Wait before retrying

# 7 - Main Execution
if __name__ == "__main__":
    print("Starting Mine Navigation Gateway...")
    # Initialize database
    db_conn = init_database()
    print("Database initialized.")
    
    # Initialize IoT Hub client
    iot_client = init_iot_client()
    
    print("Starting UDP listener...")
    # Start UDP listener in a separate thread
    udp_thread = threading.Thread(target=udp_listener, args=(db_conn,), daemon=True)
    udp_thread.start()
    
    # Run the main loop in the main thread
    try:
        main_loop(db_conn)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        if iot_client:
            iot_client.disconnect()
        db_conn.close()
        print("Cleaned up resources. Exiting.")
    print("Mine Navigation Gateway stopped.")

# 8 listener.py (for reference)
# This is a simple listener script to receive C2D messages from Azure IoT Hub
# Save this as listener.py and run it separately if needed
# It will print any messages received from the cloud

from azure.iot.device import IoTHubDeviceClient

CONNECTION_STRING = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

def message_handler(message):
    print(f"Received message from cloud: {message.data.decode('utf-8')}")
    if message.custom_properties:
        print("Custom properties:", message.custom_properties)

client.on_message_received = message_handler
client.connect()

print("Listening for C2D messages... Press Ctrl+C to stop.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopped message listener.")
finally:
    client.disconnect()
