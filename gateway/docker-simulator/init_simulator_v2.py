# This is an updated program to simulate the behaviour of moving miners and BLE beacons in a mine
# We have updated the navigation method from IMU-based trilateration using fixed anchors to BLE fingerprinting


# 1 - Imports and Configs
# The basis of the entire program 

import json
import random
import socket
import time
import math
from datetime import datetime
import sys

# Configuration
HOST = '192.168.137.100' # RPi Gateway IP
PORT = 5000
NUM_MINERS = 5
NUM_BEACONS = 12
SEND_INTERVAL = 5 # Frequent updates for navigation

# Mine Dimensions
GRID_WIDTH = 30
GRID_LENGTH = 30


# 2 - BLE Beacon Configuration
# These beacons are scattered throughout the mine
# The transmission power of each beacon varies slightly, creating unique fingerprint patterns

# More evenly distributed beacons than last time
BLE_BEACONS = {
    'beacon_001': {'x': 5, 'y': 5, 'tx_power': -60},
    'beacon_002': {'x': 5, 'y': 15, 'tx_power': -62},
    'beacon_003': {'x': 5, 'y': 25, 'tx_power': -61},
    'beacon_004': {'x': 15, 'y': 5, 'tx_power': -63},
    'beacon_005': {'x': 15, 'y': 15, 'tx_power': -59},
    'beacon_006': {'x': 15, 'y': 25, 'tx_power': -62},
    'beacon_007': {'x': 25, 'y': 5, 'tx_power': -61},
    'beacon_008': {'x': 25, 'y': 15, 'tx_power': -64},
    'beacon_009': {'x': 25, 'y': 25, 'tx_power': -60},
    'beacon_010': {'x': 10, 'y': 10, 'tx_power': -63},
    'beacon_011': {'x': 20, 'y': 20, 'tx_power': -62},
    'beacon_012': {'x': 10, 'y': 20, 'tx_power': -61}
}


# 3 - BLE Signal Simulation
# This section simulates BLE signal propagation based on distance and environmental factors

def calculate_euclidean_distance(pos1, pos2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def calculate_ble_rssi(miner_pos, beacon_info, environmental_noise=True):
    """Calculate RSSI based on distance using log-distance path loss model."""

    # i - Extract positions and Tx Power
    beacon_pos = (beacon_info['x'], beacon_info['y'])
    beacon_Pt = beacon_info['tx_power'] # in dBm

    # ii - Calculate Euclidean Distance
    distance = calculate_euclidean_distance(miner_pos, beacon_pos)
    distance = max(distance, 1.0) # Avoid log(0)

    # iii - Apply Path Loss formula : RSSI = Pt - 10*n*log10(distance)
    rssi = beacon_Pt - (10*3.5* math.log10(distance)) # n = 3.5 for indoor with obstacles

    # Optional Enhancements:
    # iv - Introduce walls/obstacles (if any)
    # walls = [Wall((x1,y1),(x2,y2),attenuation) ...]
    # walls = []
    # def line_intersects_wall(p1, p2, wall):
        # Placeholder for line-wall intersection logic
    #    return False
    
    # v - Calculate wall attenuation
    #    for wall in walls:
    #    if line_intersects_wall(miner_pos,beacon_pos,wall):
    #        rssi -= wall.attenuation

    # vi - Add Gaussian Noise if environmental_noise = True
    rssi += random.gauss(0, 2.5) # Noise with mean = 0, S.D = 2.5

    # vii - Return RSSI value between -100 to -30 dBm
    return max(-100, min(-30, rssi))


# 4 - Miner Movement Simulation
# Use IMU (specifically its accelerometer) to simulate miner movements over time
# Kinematic Equations are used

class MinerSimulator:
    def __init__(self, miner_id, start_position):
        self.miner_id = miner_id
        self.position = list(start_position)
        self.velocity = [0.0, 0.0] # m/s, 1 grid cell = 1 meter
        self.acceleration = [0.0, 0.0]
        self.last_direction_change = time.time()

    def update_position(self, dt):
        """
        Update miner position using kinematic equations
        """
        # i - Randomly change acceleration every 5-10 seconds
        if time.time() - self.last_direction_change > 5:
            self.acceleration[0] = random.uniform(-0.5, 0.5) # m/s^2
            self.acceleration[1] = random.uniform(-0.5, 0.5)
            self.last_direction_change = time.time()
        # ii - Update Velocity v = v + a*dt
        self.velocity[0] += self.acceleration[0]*dt
        self.velocity[1] += self.acceleration[1]*dt

        # iii- Cap velocity to a max speed
        max_speed = 2.0
        speed = math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
        if speed > max_speed:
            self.velocity[0] = (self.velocity[0] / speed) * max_speed
            self.velocity[1] = (self.velocity[1] / speed) * max_speed

        # iv - Update Position s = s + v*dt
        self.position[0] += self.velocity[0]*dt
        self.position[1] += self.velocity[1]*dt

        # v - Apply boundary conditions (stay within grid)
        self.position[0] = max(0, min(GRID_WIDTH-1, self.position[0]))
        self.position[1] = max(0, min(GRID_LENGTH-1, self.position[1]))

        # vi - Simulate friction (gradually reduce velocity)
        self.velocity[0] *= 0.95
        self.velocity[1] *= 0.95


# 5 - Miner Data Generation
def generate_miner_data(miner_simulator, ble_readings):
    """Generate simulated miner data for a miner device with BLE fingerprinting."""
    # Generate IMU data that correlates with actual movement
    imu_data = {
        'accel_x': round(miner_simulator.acceleration[0] + random.gauss(0, 0.1), 2),
        'accel_y': round(miner_simulator.acceleration[1] + random.gauss(0, 0.1), 2),
        'accel_z': round(9.81 + random.gauss(0, 0.1), 2),  # Gravity + noise
        'gyro_x': round(random.gauss(0, 0.05), 2),  # Simulate slight rotation
        'gyro_y': round(random.gauss(0, 0.05), 2),
        'gyro_z': round(random.gauss(0, 0.05), 2)
    }
    
    miner_data = {
        'device_id': miner_simulator.miner_id,
        'timestamp': int(datetime.now().timestamp()),
        'ble_readings': ble_readings,  # Now populated from main loop
        'imu_data': imu_data,
        'battery': random.randint(30, 100),
        'position': {  # For simulation validation - real system wouldn't have this
            'x': round(miner_simulator.position[0], 2),
            'y': round(miner_simulator.position[1], 2)
        }
    }
    return miner_data


# 6 - Main Simulation Loop
# Orchestrate the entire simulation - movement, BLE scanning, data transmission

def run_simulation():
    """Main simulation loop - Practice orchestration and timing"""

    # Initialize miner simulators with different start positions
    miners = []
    for i in range(NUM_MINERS):
        start_pos = [random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_LENGTH-1)]
        miners.append(MinerSimulator(f'miner_{i+1:02d}', start_pos))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    last_update = time.time()

    try:
        while True:
            current_time = time.time()
            dt = current_time - last_update

            for miner in miners:
                # Simulation Pipeline
                # i - Update miner position (Call Update position)
                miner.update_position(dt)
                # Note: In real system, IMU data would be used to update position. Here we simulate directly.

                # ii - Generate BLE readings for current position
                ble_readings = {}
                for beacon_id, beacon_info in BLE_BEACONS.items():
                    rssi = calculate_ble_rssi(miner.position, beacon_info)
                    # Only include beacons with strong enough signal
                    if rssi > -90:
                        ble_readings[beacon_id] = round(rssi, 2)
                # Note: In real system, BLE scan would take time. Here we assume instant scan.

                # iii - Create miner data packet
                miner_data = generate_miner_data(miner, ble_readings)

                # iv - Send via UDP
                message = json.dumps(miner_data).encode('utf-8')
                sock.sendto(message, (HOST, PORT))
                print(f"Sent {miner.miner_id}: pos({miner.position[0]:.1f}, {miner.position[1]:.1f}) with {len(ble_readings)} BLE readings")
            
            last_update = current_time
            print(f"Completed transmission at {datetime.now().strftime('%H:%M:%S')}")
            # Maintain fixed simulation step
            elapsed = time.time() - current_time
            if elapsed < SEND_INTERVAL:
                time.sleep(SEND_INTERVAL - elapsed)

    except KeyboardInterrupt:
        print("Simulation stopped by user")

    finally:
        sock.close()


# 7 - Execution

if __name__ == "__main__":
    # Allow overriding configuration from command line
    print("Usage: python init_simulator_v2.py [HOST] [PORT]")
    print("Example: python init_simulator_v2.py 192.168.137.100 5000")
    if len(sys.argv) > 1:
        HOST = sys.argv[1]
    if len(sys.argv) > 2:
        PORT = int(sys.argv[2])
    
    print(f"Starting BLE fingerprinting simulation with {NUM_MINERS} miners")
    print(f"Grid : {GRID_WIDTH}X{GRID_LENGTH} with {NUM_BEACONS} BLE beacons")
    print(f"Sending to {HOST}:{PORT} every {SEND_INTERVAL} seconds.")

    run_simulation()
