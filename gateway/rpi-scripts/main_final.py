# BLE Fingerprinting Gateway with Azure IoT Hub integration
# Python 3.7+ required
# Main dependencies: azure-iot-device, sqlite3, concurrent.futures, socket, threading

# 1 - Imports and Configs

import json
import sqlite3
import time
import socket
import threading
import os
import sys
repo_root = os. path.dirname(os.path.dirname(os.path.dirname(os.path. abspath(__file__))))
sys.path.insert(0, repo_root)
from datetime import datetime
from azure.iot.device import IoTHubDeviceClient, Message
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path for algorithm imports
sys.path.insert(0, os. path.dirname(os.path. dirname(os.path.abspath(__file__))))

# Import algorithm modules
from algorithms.rssi_preprocessing import RSSIPreprocessor
from algorithms.fingerprint_matching import FingerprintMatcher
from algorithms.state_management import MinerStateManager
from algorithms.maze_creation import generate_floor_plan, create_digitized_maze_data_cartesian
from algorithms. solver_and_orientation import get_navigation_stack
from algorithms.navigation import convert_coordinate_stack_to_move_sequence

# Configuration
CONNECTION_STRING = os. getenv("IOTHUB_DEVICE_CONNECTION_STRING")
UDP_IP = '0.0.0.0'
UDP_PORT = 5000

# Mine Configuration
GRID_WIDTH = 12  # Matches maze_creation.py dimensions
GRID_HEIGHT = 16  # Matches maze_creation.py dimensions
SAFE_ZONE = (0, 15)

# Algorithm Configuration
RADIO_MAP_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "algorithms", "radio_map.json")
BEACON_IDS = ['B1', 'B2', 'B3']
MIN_CONFIDENCE_THRESHOLD = 0.4
MOVE_LIMIT_PER_CYCLE = 5

# State Management
db_lock = threading.Lock()
iot_client = None

# Algorithm Components (initialized in init_algorithms)
rssi_preprocessor = None
fingerprint_matcher = None
miner_state_manager = None
maze_data = None

# Thread Pool for handling multiple miners
thread_pool = ThreadPoolExecutor(max_workers=4)


# 2 - Algorithm Initialization

def init_algorithms():
    """Initialize all algorithm components."""
    global rssi_preprocessor, fingerprint_matcher, miner_state_manager, maze_data
    
    print("Initializing algorithm components...")
    
    # Initialize RSSI preprocessor
    rssi_preprocessor = RSSIPreprocessor(
        alpha=0.3,
        outlier_threshold_db=15,
        min_samples=5,
        max_history=10
    )
    print("  - RSSI Preprocessor initialized")
    
    # Initialize miner state manager with expected miner IDs
    miner_state_manager = MinerStateManager(
        expected_miner_ids=['M01', 'M02', 'M03', 'M04', 'M05']
    )
    print("  - Miner State Manager initialized")
    
    # Initialize maze data from floor plan
    visual_grid = generate_floor_plan()
    maze_data = create_digitized_maze_data_cartesian(visual_grid)
    print(f"  - Maze data initialized: {maze_data['dimensions']} grid with {len(maze_data['exits'])} exits")
    
    # Initialize fingerprint matcher if radio map exists
    if os. path.exists(RADIO_MAP_FILE):
        try:
            fingerprint_matcher = FingerprintMatcher(RADIO_MAP_FILE)
            print(f"  - Fingerprint Matcher initialized from {RADIO_MAP_FILE}")
        except Exception as e:
            print(f"  - Warning: Failed to load fingerprint matcher: {e}")
            fingerprint_matcher = None
    else:
        print(f"  - Warning: Radio map not found at {RADIO_MAP_FILE}")
        print("    Position estimation will fall back to simulator data")
        fingerprint_matcher = None
    
    print("Algorithm initialization complete.")


# 3 - Azure IoT Hub Setup

def init_iot_client():
    """Initialize & return an IoT Hub Client."""
    if not CONNECTION_STRING:
        print("Warning: IOTHUB_DEVICE_CONNECTION_STRING not set. Azure messaging disabled.")
        return None
    
    try:
        client = IoTHubDeviceClient. create_from_connection_string(CONNECTION_STRING)
        client.connect()
        print("IoT Hub Client connected")
        return client
    except Exception as e:
        print(f"Failed to connect to IoT Hub: {e}")
        return None


def send_to_azure(message_body):
    """Send a message to Azure IoT Hub."""
    global iot_client
    if not iot_client:
        # Silent skip if no client - already warned at startup
        return
    
    try:
        message = Message(json.dumps(message_body))
        message.content_type = "application/json"
        message.content_encoding = "utf-8"
        iot_client.send_message(message)
        print(f"Message sent to Azure: {message_body. get('device_id', 'gateway')}")
    except Exception as e:
        print(f"Failed to send message to Azure: {e}")
        # Try to reconnect
        try:
            iot_client.disconnect()
            iot_client = init_iot_client()
        except Exception as conn_e:
            print(f"Failed to reconnect to IoT Hub: {conn_e}")


# 4 - Database Setup

def init_database():
    """Initialize the SQLite database for BLE fingerprinting system."""
    db_path = os.path.join(os.path.dirname(__file__), 'mine_nav.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    
    # Create miner_telemetry table with BLE readings and estimated position
    cursor. execute('''
        CREATE TABLE IF NOT EXISTS miner_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            timestamp TEXT,
            ble_readings TEXT,
            imu_data TEXT,
            battery INTEGER,
            estimated_x REAL,
            estimated_y REAL,
            confidence REAL,
            path_length INTEGER,
            status TEXT
        )
    ''')
    
    # Create navigation_commands table to store paths and commands
    cursor. execute('''
        CREATE TABLE IF NOT EXISTS navigation_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            timestamp TEXT,
            command TEXT,
            path_coordinates TEXT,
            move_sequence TEXT
        )
    ''')
    
    # Create miner_states table for current state tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS miner_states (
            device_id TEXT PRIMARY KEY,
            current_x REAL,
            current_y REAL,
            goal_x REAL,
            goal_y REAL,
            status TEXT,
            confidence REAL,
            last_update TEXT
        )
    ''')
    
    # Add indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_miner_id ON miner_telemetry (device_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON miner_telemetry (timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_nav_device ON navigation_commands (device_id)')
    
    conn.commit()
    print(f"Database initialized at {db_path}")
    return conn


# 5 - Position Estimation using Fingerprinting

def estimate_miner_position(ble_readings, miner_id=None):
    """
    Estimate miner position using the fingerprint matching algorithm pipeline.
    
    Args:
        ble_readings: Dict of beacon_id -> rssi_value or beacon_id -> [rssi_values]
        miner_id: Optional miner identifier for state tracking
    
    Returns:
        Tuple of (position, confidence) where position is (x, y) or None
    """
    global fingerprint_matcher, rssi_preprocessor, miner_state_manager
    
    if not ble_readings:
        return None, 0.0
    
    if not fingerprint_matcher:
        # No radio map available - cannot estimate position
        return None, 0.0
    
    # Convert ble_readings to format expected by preprocessor
    # Handle both single values and lists of values
    raw_samples = {}
    for beacon_id, value in ble_readings.items():
        if beacon_id in BEACON_IDS:
            if isinstance(value, list):
                raw_samples[beacon_id] = value
            else:
                raw_samples[beacon_id] = [value]
    
    # Ensure all beacons are represented
    for beacon_id in BEACON_IDS:
        if beacon_id not in raw_samples:
            raw_samples[beacon_id] = []
    
    # Get previous smoothed values from state manager if available
    previous_smoothed = None
    if miner_id and miner_state_manager:
        miner_state = miner_state_manager.get_miner_state(miner_id)
        if miner_state and miner_state.get('smoothed_rssi'):
            previous_smoothed = miner_state['smoothed_rssi']
    
    # Step 1: Preprocess RSSI data
    processed = rssi_preprocessor.process_miner_rssi(
        miner_id or "unknown",
        raw_samples,
        previous_smoothed=previous_smoothed
    )
    
    # Update smoothed RSSI in state manager
    if miner_id and miner_state_manager:
        for beacon_id, value in processed['processed_rssi'].items():
            miner_state_manager. update_smoothed_rssi(miner_id, beacon_id, value)
    
    # Check if preprocessing confidence is too low
    if processed['overall_confidence'] < 0.3:
        print(f"  Low preprocessing confidence for {miner_id}: {processed['overall_confidence']:. 2f}")
        return None, processed['overall_confidence']
    
    # Step 2: Use fingerprint matcher to estimate location
    location_result = fingerprint_matcher.locate_miner(
        processed['processed_rssi'],
        miner_id=miner_id
    )
    
    if location_result['valid']:
        position = (
            location_result['location']['x'],
            location_result['location']['y']
        )
        confidence = location_result['confidence']
        print(f"  Position estimated for {miner_id}: ({position[0]}, {position[1]}) conf={confidence:.2f}")
        return position, confidence
    
    print(f"  Localization failed for {miner_id}: {location_result['status']}")
    return None, 0.0


# 6 - Pathfinding and Navigation

def calculate_escape_path(current_position, miner_id):
    """
    Calculate path to nearest exit using BFS solver.
    
    Args:
        current_position: Tuple (x, y) of current location
        miner_id: Miner identifier
    
    Returns:
        List of (x, y) coordinates representing path to exit
    """
    global maze_data
    
    if not maze_data or not current_position:
        return []
    
    start_x = int(round(current_position[0]))
    start_y = int(round(current_position[1]))
    
    # Validate position is within grid
    W, H = maze_data['dimensions']
    if not (0 <= start_x < W and 0 <= start_y < H):
        print(f"  Warning: Position ({start_x}, {start_y}) outside grid bounds")
        return []
    
    # Get coordinate path to nearest exit
    path = get_navigation_stack(miner_id, start_x, start_y, maze_data)
    
    if path:
        print(f"  Path calculated for {miner_id}: {len(path)} steps to exit")
    else:
        print(f"  No path found for {miner_id} from ({start_x}, {start_y})")
    
    return path


def get_move_instructions(path, current_position, current_orientation='N'):
    """
    Convert coordinate path to movement instructions.
    
    Args:
        path: List of (x, y) coordinates
        current_position: Starting (x, y) position
        current_orientation: Current facing direction ('N', 'E', 'S', 'W')
    
    Returns:
        List of move commands ('F', 'L', 'R')
    """
    if not path:
        return []
    
    start_x = int(round(current_position[0]))
    start_y = int(round(current_position[1]))
    
    move_sequence = convert_coordinate_stack_to_move_sequence(
        path,
        start_x,
        start_y,
        start_facing=current_orientation
    )
    
    return move_sequence


# 7 - State Update Functions

def update_miner_state(miner_id, position, confidence, imu_data, ble_readings, 
                       path, move_sequence, db_conn):
    """
    Update miner state in both state manager and database. 
    """
    global miner_state_manager
    
    timestamp = datetime.now(). isoformat()
    
    # Update state manager
    if miner_state_manager and position:
        miner_state_manager.update_miner_location(
            miner_id, position, confidence, timestamp
        )
        
        # Update instruction queue
        if move_sequence:
            miner_state_manager.update_instruction_queue(miner_id, move_sequence)
    
    # Log to database
    with db_lock:
        cursor = db_conn. cursor()
        
        # Insert telemetry record
        cursor.execute('''
            INSERT INTO miner_telemetry 
            (device_id, timestamp, ble_readings, imu_data, battery, 
             estimated_x, estimated_y, confidence, path_length, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            miner_id,
            timestamp,
            json.dumps(ble_readings),
            json. dumps(imu_data),
            imu_data.get('battery', 100),
            position[0] if position else None,
            position[1] if position else None,
            confidence,
            len(path) if path else 0,
            miner_state_manager.get_miner_state(miner_id). get('status', 'UNKNOWN') if miner_state_manager else 'UNKNOWN'
        ))
        
        # Insert navigation command if we have moves
        if move_sequence:
            cursor.execute('''
                INSERT INTO navigation_commands
                (device_id, timestamp, command, path_coordinates, move_sequence)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                miner_id,
                timestamp,
                'NAVIGATE_TO_EXIT',
                json.dumps([(int(x), int(y)) for x, y in path] if path else []),
                json.dumps(move_sequence[:MOVE_LIMIT_PER_CYCLE])
            ))
        
        # Update miner_states table
        if position:
            # Find nearest exit for goal
            goal = maze_data['exits'][0] if maze_data and maze_data['exits'] else (0, 0)
            
            cursor.execute('''
                INSERT OR REPLACE INTO miner_states
                (device_id, current_x, current_y, goal_x, goal_y, status, confidence, last_update)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                miner_id,
                position[0],
                position[1],
                goal[0],
                goal[1],
                miner_state_manager. get_miner_state(miner_id).get('status', 'ACTIVE') if miner_state_manager else 'ACTIVE',
                confidence,
                timestamp
            ))
        
        db_conn.commit()
    
    print(f"Updated state for {miner_id}: pos=({position[0]:.1f}, {position[1]:.1f}), conf={confidence:.2f}" if position else f"Updated state for {miner_id}: no position")


# 8 - Message Processing

def process_miner_message(message_data, db_conn):
    """
    Process a single miner message through the full algorithm pipeline.
    
    Pipeline:
    1. Parse incoming message
    2.  Preprocess RSSI data
    3.  Estimate position via fingerprinting
    4. Update state manager
    5. Calculate escape path
    6. Generate move instructions
    7.  Store in database
    8. Send to Azure IoT Hub
    """
    global miner_state_manager
    
    try:
        message = json.loads(message_data. decode('utf-8'))
        miner_id = message.get('device_id')
        ble_readings = message.get('ble_readings', {})
        imu_data = message.get('imu_data', {})
        
        if not miner_id:
            print("Invalid message: missing device_id")
            return
        
        print(f"\nProcessing message from {miner_id}...")
        
        # Step 1: Estimate position using fingerprinting pipeline
        position, confidence = estimate_miner_position(ble_readings, miner_id)
        
        # Fallback to simulator position if available and fingerprinting failed
        simulator_position = message.get('position')
        if not position and simulator_position:
            position = (simulator_position['x'], simulator_position['y'])
            confidence = 1.0
            print(f"  Using simulator position: ({position[0]}, {position[1]})")
        
        # Initialize path and move sequence
        path = []
        move_sequence = []
        
        if position:
            # Step 2: Check confidence threshold
            if confidence >= MIN_CONFIDENCE_THRESHOLD:
                # Step 3: Calculate escape path
                path = calculate_escape_path(position, miner_id)
                
                if path:
                    # Step 4: Get current orientation from state
                    current_orientation = 'N'
                    if miner_state_manager:
                        miner_state = miner_state_manager.get_miner_state(miner_id)
                        if miner_state:
                            current_orientation = miner_state.get('estimated_orientation', 'N')
                    
                    # Step 5: Generate move instructions
                    move_sequence = get_move_instructions(path, position, current_orientation)
                    
                    # Limit moves per cycle
                    moves_to_send = move_sequence[:MOVE_LIMIT_PER_CYCLE]
                    print(f"  Move sequence: {' '. join(moves_to_send)} ({len(move_sequence)} total)")
            else:
                print(f"  Confidence {confidence:. 2f} below threshold {MIN_CONFIDENCE_THRESHOLD}")
            
            # Step 6: Update state and database
            update_miner_state(
                miner_id, position, confidence, imu_data, ble_readings,
                path, move_sequence, db_conn
            )
        else:
            print(f"  Could not determine position for {miner_id}")
        
        # Step 7: Prepare and send Azure payload
        azure_payload = {
            "device_id": miner_id,
            "timestamp": datetime.now().isoformat(),
            "device_timestamp": message.get("timestamp"),
            "position": {
                "x": position[0],
                "y": position[1]
            } if position else None,
            "confidence": confidence,
            "ble_readings": ble_readings,
            "imu_data": imu_data,
            "navigation": {
                "path_length": len(path),
                "next_moves": move_sequence[:MOVE_LIMIT_PER_CYCLE] if move_sequence else [],
                "status": "NAVIGATING" if path else "NO_PATH"
            } if position else None,
            "miner_status": miner_state_manager.get_miner_state(miner_id). get('status', 'UNKNOWN') if miner_state_manager and position else 'NO_POSITION'
        }
        
        # Add simulator position for comparison/debugging
        if simulator_position:
            azure_payload["simulator_position"] = simulator_position
        
        # Add battery level
        battery_value = message.get("battery", imu_data.get("battery", None))
        if battery_value is not None:
            azure_payload["battery"] = battery_value
        
        send_to_azure(azure_payload)
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse message JSON: {e}")
    except Exception as e:
        print(f"Error processing miner message: {e}")
        import traceback
        traceback.print_exc()


# 9 - UDP Listener

def udp_listener(db_conn):
    """Listen for UDP messages from miners and process them using thread pool."""
    sock = socket.socket(socket.AF_INET, socket. SOCK_DGRAM)
    sock. bind((UDP_IP, UDP_PORT))
    print(f"Listening for UDP messages on {UDP_IP}:{UDP_PORT}")
    
    try:
        while True:
            try:
                data, addr = sock.recvfrom(4096)  # Increased buffer for larger messages
                # Submit to thread pool for processing
                thread_pool.submit(process_miner_message, data, db_conn)
            except KeyboardInterrupt:
                print("UDP listener stopped.")
                break
            except Exception as e:
                print(f"Error in UDP listener: {e}")
    finally:
        sock.close()


# 10 - Main Loop

def main_loop(db_conn):
    """Main loop that runs monitoring and periodic status updates."""
    global miner_state_manager
    
    print("\nStarting main monitoring loop...")
    
    while True:
        try:
            # Get status of all miners
            if miner_state_manager:
                active_miners = miner_state_manager. get_active_miners()
                inactive_miners = miner_state_manager. get_inactive_miners()
                avg_confidence = miner_state_manager.calculate_average_confidence()
                
                # Prepare miner data for Azure
                miners_data = miner_state_manager.get_all_miners_data_for_azure()
            else:
                active_miners = []
                inactive_miners = []
                avg_confidence = 0.0
                miners_data = []
            
            # Send gateway status update
            status_message = {
                "message_type": "gateway_status",
                "gateway_id": "rpi_mine_gateway",
                "timestamp": datetime.now(). isoformat(),
                "miners_tracked": len(active_miners),
                "miners_active": active_miners,
                "miners_inactive": inactive_miners,
                "average_confidence": round(avg_confidence, 3),
                "miners_data": miners_data,
                "status": "operational",
                "maze_exits": maze_data['exits'] if maze_data else []
            }
            send_to_azure(status_message)
            
            # Log status locally
            print(f"\n[STATUS] Active miners: {len(active_miners)}, Avg confidence: {avg_confidence:.2f}")
            for miner_id in active_miners:
                state = miner_state_manager.get_miner_state(miner_id)
                if state and state['current_location']:
                    loc = state['current_location']
                    print(f"  {miner_id}: ({loc[0]:.1f}, {loc[1]:.1f}) - {state['status']}")
            
            time.sleep(10)  # Status update interval
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)


# 11 - Entry Point

if __name__ == "__main__":
    print("=" * 60)
    print("Mine Disaster Response - BLE Fingerprinting Gateway")
    print("=" * 60)
    
    # Initialize components
    print("\n[1/4] Initializing database...")
    db_conn = init_database()
    
    print("\n[2/4] Initializing Azure IoT Hub client...")
    iot_client = init_iot_client()
    
    print("\n[3/4] Initializing algorithm components...")
    init_algorithms()
    
    print("\n[4/4] Starting UDP listener...")
    udp_thread = threading.Thread(target=udp_listener, args=(db_conn,), daemon=True)
    udp_thread.start()
    
    print("\n" + "=" * 60)
    print("Gateway started successfully!")
    print("=" * 60)
    
    # Start main loop
    try:
        main_loop(db_conn)
    except KeyboardInterrupt:
        print("\n\nShutting down gateway...")
    finally:
        print("Cleaning up resources...")
        if iot_client:
            try:
                iot_client.disconnect()
            except Exception:
                pass
        db_conn.close()
        thread_pool.shutdown(wait=True)
        print("Gateway stopped.")
    