import json
import random
import socket
import time
from datetime import datetime
import sys

# Configuration - May be overridden by environment variables inside Docker
HOST = '192.168.137.100'
PORT = 5000
NUM_MINERS = 5
NUM_ANCHORS = 3
SEND_INTERVAL = 15 # seconds between transmissions

# Fixed Anchor Positions (known coordinates in the mine)

ANCHOR_POSITIONS = {
    'anchor_entrance': {'x': 1 , 'y' : 1},
    'anchor_tunnel1' : {'x': 3 , 'y' : 2},
    'anchor_tunnel2' : {'x': 5 , 'y' : 5}
}

def generate_miner_data(device_id):
    """"Generate simulated data for a miner device."""
    return {
        'device_id': device_id,
        'timestamp': int(datetime.now().timestamp()),
        'accel_x' : round(random.uniform(-2, 2), 2),
        'accel_y' : round(random.uniform(-2, 2), 2),
        'accel_z' : round(random.uniform(7, 11), 2),
        'gyro_x' : round(random.uniform(-0.5, 0.5), 2),
        'gyro_y' : round(random.uniform(-0.5, 0.5), 2),
        'gyro_z' : round(random.uniform(-0.5, 0.5), 2),
        'rssi' : random.randint(-90, -30),
        'battery' : random.randint(20, 100)
    }

def generate_anchor_data(device_id,position):
    """Generate simulated data for an anchor device."""
    return {
        'device_id': device_id,
        'timestamp': int(datetime.now().timestamp()),
        'fixed_x': position['x'],
        'fixed_y': position['y'],
        'rssi' : random.randint(-60, -15)
    }

def send_data():
    """Main function to send simulated data to the server."""
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        while True:
            # Send data from all miners
            for i in range(NUM_MINERS):
                miner_id = f'miner_{i+1:02d}'
                miner_data = generate_miner_data(miner_id)
                message = json.dumps(miner_data).encode('utf-8')
                sock.sendto(message, (HOST, PORT))
                print(f'Sent miner data: {message.decode()}')

            # Send data from all anchors
            for anchor_id, position in ANCHOR_POSITIONS.items():
                anchor_data = generate_anchor_data(anchor_id, position)
                message = json.dumps(anchor_data).encode('utf-8')
                sock.sendto(message, (HOST, PORT))
                print(f'Sent anchor data: {message.decode()}')

            # Wait before sending the next batch
            time.sleep(SEND_INTERVAL)
    except KeyboardInterrupt:
        print("Simulation stopped by user.")
    finally:
        sock.close()
        print("Socket closed.")
        sys.exit(0)

if __name__ == '__main__':
    # Allow overriding configuration from environment variables
    if len(sys.argv) > 1:
        HOST = sys.argv[1]
    if len(sys.argv) > 2:
        PORT = int(sys.argv[2])
    
    print(f"Starting simulation. Sending data to {HOST}:{PORT}")
    send_data()




