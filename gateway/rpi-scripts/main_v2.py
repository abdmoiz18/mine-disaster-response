# Updated script for BLE fingerprinting gateway with Azure IoT Hub integration

# 1 - Imports and Configs

import json
import sqlite3
import time
import socket
import threading
import os
from datetime import datetime
from azure.iot.device import IoTHubDeviceClient, Message
from concurrent.futures import ThreadPoolExecutor

# Configuration
CONNECTION_STRING = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
UDP_IP = '0.0.0.0'
UDP_PORT = 5000

# Mine Configuration
GRID_WIDTH = 30
GRID_LENGTH = 30
SAFE_ZONE = (0, 15)

# State Management
current_miner_states = {} 
db_lock = threading.Lock()
iot_client = None

# Thread Pool for handling multiple miners
thread_pool = ThreadPoolExecutor(max_workers=4)


# 2 - Azure IoT Hub Setup

def __init__iot_client():
    # Initialize & return an IoT Hub Client
    try:
        client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
        client.connect()
        print("IoT Hub Client connected")
        return client
    except Exception as e:
        print(f"Failed to connect to IoT Hub: {e}")
        return None

def send_to_azure(message_body):
    # Send a message to Azure IoT Hub
    global iot_client
    if not iot_client:
        print("IoT Client not initiated. Skipping message.")
        return
    
    try:
        message = Message(json.dumps(message_body))
        iot_client.send_message(message)
        print(f"Message sent to Azure: {message_body}")
    except Exception as e:
        print(f"Failed to send message to Azure: {e}")
        # Try to reconnect
        try:
            iot_client.disconnect()
            iot_client = __init__iot_client()
        except Exception as conn_e:
            print(f"Failed to reconnect to IoT Hub: {conn_e}")


# 3 - Database Schema Update
# Update database to store BLE fingerprint data and navigation states instead of single RSSI values

def init_database():
    # Initialize the SQLite database for BLE fingerprinting system
    conn = sqlite3.connect('mine_nav.db', check_same_thread=False)
    cursor = conn.cursor()
    # i - Create miner_telemetry_table with BLE readings (JSON) and estimated position
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS miner_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            timestamp TEXT,
            ble_readings TEXT,  -- JSON string of beacon_id to RSSI
            imu_data TEXT,      -- JSON string of IMU data
            battery INTEGER,
            estimated_x REAL,
            estimated_y REAL,
            confidence REAL
        )
    ''')
    # ii - Create navigation_commands table to store paths and goals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS navigation_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            timestamp TEXT,
            command TEXT
        )
    ''')
    # iii - Create miner_states table to track current states
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS miner_states (
            device_id TEXT PRIMARY KEY,
            current_x REAL,
            current_y REAL,
            goal_x REAL,
            goal_y REAL,
            last_update TEXT
        )
    ''')
    # iv - Add indexes on miner_id and timestamp columns
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_miner_id ON miner_telemetry (device_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON miner_telemetry (timestamp)')
    # v - Consider a fingerprint database table for kNN model (optional)
    # Placeholder for future fingerprint database
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fingerprint_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            fingerprint_data TEXT,
            last_update TEXT
        )
    ''')
    conn.commit()
    return conn


# 4 - BLE Fingerprinting Integration
# Process incoming BLE fingerprint data and estimate position using kNN or other algorithms

def estimate_miner_position(ble_readings):
    # Estimated position based on kNN or similar algorithm. Integrate with fingerprinting algorithm.
    # i - Validate BLE readings (beacons, RSSI values)
    if not ble_readings:
        return None, 0.0  # No valid readings
    # ii - Call kNN/algorithm to estimate position and confidence
    try:
        # Call ML Model here (stubbed)
        prediction, confidence = self.model.predict(ble_readings)
        # Handle low confidence cases using IMU readings and the previous cached prediction
        if confidence < 0.5:
            print("Low confidence in position estimate, using IMU data for correction.")
            # Apply IMU-based correction (stubbed)
            prediction = self.apply_imu_correction(prediction)
            confidence += 0.2  # Boost confidence slightly
        return prediction, confidence
    except Exception as e:
        print(f"Error in position estimation: {e}")
        return None, 0.0

def update_miner_state(miner_id, position, confidence, imu_data):
    # Update miner state with new position estimate. State management and IMU validation
    # 1 - Update current_miner_states dictionary
    global current_miner_states
    current_miner_states[miner_id] = {
        'current_position': position,
        'confidence': confidence,
        'imu_data': imu_data,
        'last_update': datetime.now().isoformat()
    }
    # 2 - Store position history for tracking
    position_history = current_miner_states[miner_id].get('position_history', [])
    position_history.append({
        'timestamp': datetime.now().isoformat(),
        'position': position,
        'confidence': confidence
    })
    current_miner_states[miner_id]['position_history'] = position_history
    # 3 - Use IMU data to validate movement (optional)
    # 4 - Update database with new telemetry
    with db_lock:
        cursor = db_conn.cursor()
        cursor.execute('''
            INSERT INTO miner_telemetry (device_id, timestamp, ble_readings, imu_data, battery, estimated_x, estimated_y, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (miner_id, datetime.now().isoformat(), json.dumps(ble_readings), json.dumps(imu_data), imu_data.get('battery', 100), position[0], position[1], confidence))
        conn.commit()
    # 5 - Check if miner needs new navigation instructions
    if miner_id in current_miner_states and 'goal_position' in current_miner_states[miner_id]:
        goal = current_miner_states[miner_id]['goal_position']
        if distance(position, goal) < 2.0:  # Within 2 meters of goal
            print(f"Miner {miner_id} has reached the goal at {goal}")
            del current_miner_states[miner_id]['goal_position']  # Clear goal
            send_navigation_command(miner_id, None)  # Send stop command
    pass


# 5 - Navigation and Pathfinding
# Calculate and manage navigation paths using A* algorithm and handle miner movement

class NavigationManager:
    def __init__(self):
        self.path_cache = {}
        self.miner_goals = {}
    
    def update_miner_goal(self, miner_id, goal_position):
        # Update miner goal and recalculate path if needed
        self.miner_goals[miner_id] = goal_position
        self.path_cache[miner_id] = None  # Invalidate cached path
        self.recalculate_path(miner_id)
        pass
    
    def get_next_navigation_step(self, miner_id, current_position):
        # i - Check for a cached path for this miner and goal
        cache_key = f"{miner_id}_{self.miner_goals.get(miner_id)}"
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]
        # ii - If no cached path or miner deviated, recalculate using A* and cache it
        path = self.recalculate_path(miner_id)
        if path:
            self.path_cache[cache_key] = path
            return path.pop(0)  # Return next step
        return None

        # Placeholder function for movement, replace with A* pathfinding later
        def a_star_pathfinding(start, goal, grid):
    # Stub function for A* pathfinding algorithm
    # Return a list of waypoints from start to goal
            return [start, goal]

        # iii - Find the current position in path, return only the next step
        try:
            current_index = path.index(current_position)
            return path[current_index + 1] if current_index + 1 < len(path) else None
        except ValueError:
            return path[0] if path else None  # If not found, return first step
        
        # v - Handle miner deviations
        
    
    def handle_miner_deviation(self, miner_id, expected_position):
        # Recalculate path if miner deviates significantly
        current_position = current_miner_states[miner_id]['current_position']
        if distance(current_position, expected_position) > 3.0:  # More than 3 meters off
            print(f"Miner {miner_id} deviated from path, recalculating...")
            self.recalculate_path(miner_id)
        pass

    def recalculate_path(self, miner_id):
        # Recalculate path using A* algorithm
        if miner_id not in current_miner_states or miner_id not in self.miner_goals:
            return None
        start = current_miner_states[miner_id]['current_position']
        goal = self.miner_goals[miner_id]
        path = a_star_pathfinding(start, goal, grid=None)  # Replace grid with actual mine layout
        return path


# 6 - UDP Listener with Thread Pool
# Handle multiple miner connections concurrently using thread pool instead of simple threading

def process_miner_message(message_data, db_conn):
    # Process a single miner message called by thread pool
    global current_miner_states
    # i - Validate message structure
    try:
        message = json.loads(message_data)
        miner_id = message.get('device_id')
        if not miner_id or 'ble_readings' not in message or 'imu_data' not in message:
            print("Invalid message format")
            return
        ble_readings = message['ble_readings']
        imu_data = message['imu_data']
    except json.JSONDecodeError:
        print("Received invalid JSON")
        return
    # ii - Extract BLE readings and IMU data
    position, confidence = estimate_miner_position(ble_readings)
    if position:
        update_miner_state(miner_id, position, confidence, imu_data)
    else:
        print(f"Could not estimate position for miner {miner_id}")
        return
    # iii - Estimate position using BLE fingerprinting
    position, confidence = estimate_miner_position(ble_readings)
    if position:
        update_miner_state(miner_id, position, confidence, imu_data)
    else:
        print(f"Could not estimate position for miner {miner_id}")
        return
    # iv - Update miner state
    update_miner_state(miner_id, position, confidence, imu_data)
    
    # v - Log to database
    log_miner_data(db_conn, miner_id, position, confidence, imu_data)

    # vi - Send to Azure IoT Hub
    send_to_azure({
        'device_id': miner_id,
        'timestamp': datetime.now().isoformat(),
        'position': position,
        'confidence': confidence,
        'ble_readings': ble_readings,
        'imu_data': imu_data
    })
    pass

def udp_listener(db_conn):
    # Listen for incoming UDP messages from miners
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"Listening for UDP messages on {UDP_IP}:{UDP_PORT}")
    
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            # Submit to thread pool for processing
            thread_pool.submit(process_miner_message, data, db_conn)
    except KeyboardInterrupt:
        print("UDP listener stopped.")
    finally:
        sock.close()
        thread_pool.shutdown()

# 7 - Main Loop and Execution

def main_loop(db_conn):
    # Main loop that runs navigation and monitoring
    navigation_mgr = NavigationManager()

    while True:
        try:
            # Process each miner's navigation needs
            for miner_id, state in current_miner_states.items():
                if state.get('goal_position'):
                    next_step = navigation_mgr.get_next_navigation_step(miner_id, state['current_position'])
                    if next_step:
                        send_navigation_command(miner_id, next_step)
            
            # Send periodic status updates to Azure
            status_message = {
                "gateway_id" : "rpi_mine_entrance",
                "timestamp" : datetime.now().isoformat(),
                "miners_tracked" : len(current_miner_states),
                "status" : "operational" 
            }
            send_to_azure(status_message)
            time.sleep(10)
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("Starting BLE Fingerprinting Gateway...")
    db_conn = init_database()
    iot_client = __init__iot_client()

    print(f"Starting UDP listener with thread pool...")
    udp_thread = threading.Thread(target=udp_listener, args=(db_conn,), daemon=True)
    udp_thread.start()

    # Run main loop
    try:
        main_loop(db_conn)
    except KeyboardInterrupt:
        print("Shutting down gateway...")
    finally:
        if iot_client:
            iot_client.disconnect()
        db_conn.close()
        print("Gateway shut down.")
