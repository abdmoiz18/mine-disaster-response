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

BLE_BEACONS = {
    'beacon_001' : {'x': 2, 'y' : 3, 'tx_power' : -65},
    'beacon_002' : {'x': 8, 'y' : 25, 'tx_power' : -63},
    'beacon_003' : {'x': 15, 'y' : 8, 'tx_power' : -66},
    'beacon_004' : {'x': 22, 'y' : 18, 'tx_power' : -68},
    'beacon_005' : {'x': 5, 'y' : 15, 'tx_power' : -65},
    'beacon_006' : {'x': 28, 'y' : 5, 'tx_power' : -67},
    'beacon_007' : {'x': 12, 'y' : 28, 'tx_power' : -64},
    'beacon_008' : {'x': 25, 'y' : 12, 'tx_power' : -67},
    'beacon_009' : {'x': 18, 'y' : 22, 'tx_power' : -61},
    'beacon_010' : {'x': 7, 'y' : 10, 'tx_power' : -62},
    'beacon_011' : {'x': 20, 'y' : 7, 'tx_power' : -69},
    'beacon_012' : {'x': 10, 'y' : 20, 'tx_power' : -66}
}


# 3 - BLE Signal Simulation
# This section simulates BLE signal propagation based on distance and environmental factors

def calculate_ble_rssi(miner_pos, beacon_pos, tx_power, walls, environmental_noise=True):
    """Calculate RSSI based on distance using log-distance path loss model."""
    # i - Calculate Euclidean Distance
    distance = calculate_distance(miner_pos, beacon_pos)
    # ii - Apply Path Loss formula : RSSI = Pt - 10*n*log10(distance)
    rssi = beacon_Pt - (10*3.5* math.log10(distance))
    # iii - Calculate wall attenuation
    #    for wall in walls:
    #    if line_intersects_wall(miner_pos,beacon_pos,wall):
    #        rssi -= wall.attenuation
    # iv - Add Gaussian Noise if environmental_noise = True
    rssi += random.gauss(0, 2.5) # Noise with mean = 0, S.D = 2.5
    # v - Return RSSI value between -100 to -30 dBm
    return max(-100, min(-30, rssi))
    pass

# Later, use more realistic models. Take environmental conditions into account. Real BLE is noisy


# 4 - Miner Movement Simulation
# Use IMU (specifically its accelerometer) to simulate miner movements over time
# Kinematic Equations are used

class MinerSimulator:
    def __init__(self, miner_id, start_position):
        self.miner_id = miner_id
        self.position = start_position
        self.velocity = [0,0] # m/s, 1 grid cell = 1 meter
        self.acceleration = [0,0]
    
    def update_position(self, dt):
        """
        Update miner position using kinematic equations
        """
        # i - Update Velocity v = v + a*dt
        self.velocity[0] += new_acceleration[0]*dt
        self.velocity[1] += new_acceleration[1]*dt
        # ii - Update Position s = s + v*dt
        self.position[0] += self.velocity[0]*dt
        self.position[1] += self.velocity[1]*dt
        # iii - Apply boundary conditions
        pass
    
# Note for later - Occasionally change acceleration for realistic movements.
# Avoid making movement perfectly linear. Do not ignore mine layout constraints
# Do not decouple IMU from actual position


# 5 - Miner Data Generation

def generate_miner_data(miner_simulator):
    """Generate simulated miner data for a miner device with BLE fingerprinting"""
    miner_data = {
        'device_id' : miner_simulator.miner_id,
        'timestamp' : int(datetime.now().timestamp())
        'ble_readings' : {}
        'imu_data' : { 
            'accel_x' : 0, 'accel_y' : 0, 'accel_z' : 9.81,
            'gyro_x' : 0, 'gyro_y' : 0, 'gyro_z' : 0     
        },
        'battery' : random.randint(30,100),
        'position' : { # To validate simulation. A real system wouldn't generate this
            'x' : miner_simulator.position[0],
            'y' : miner_simulator.position[1]
        }
    }

    # BLE Readings will be filled in the main loop
    return miner_data


# 6 - Main Simulation Loop
# Orchestrate the entire simulation - movement, BLE scanning, data transmission

def run_simulation():
    """
    Main simulation loop - Practice orchestration and timing
    """

    # Initialize miner simulators with different start positions
    miners = []
    for i in range(NUM_MINERS):
        start_pos = [random.randint(0, GRID_WIDTH), random.randint(0, GRID_LENGTH)]
        miners.append(MinerSimulator(f'miner_{i+02d}', start_pos))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    last_update = time.time()

    try:
        while True:
            current_time = time.time()
            dt = current_time - last_update

            for miner in miners:
                # Simulation Pipeline
                # i - Update miner position (Call Update position)
                self.update_position(dt)
                # ii - Generate BLE readings for current position
                self.generate_miner_data()
                # iii - Create miner data packet
                self.
                # iv - Send via UDP
                for i in range(NUM_MINERS):
                    miner_id = f'miner_{i+1:02d}'
                    miner_data = generate_miner_data(miner_id)
                    message = json.dumps(miner_data).encode('utf-8')
                    sock.sendto(message, (HOST, PORT))
                    print(f'Sent miner data: {message.decode()}')
                pass
            
            last_update = current_time
            time.sleep(SEND_INTERVAL)

    except KeyboardInterrupt:
        print("Simulation stopped by user")

    finally:
        sock.close()

# Later
# Use consistent time steps for physics, seperate concerns (movement vs communication)
# Add simulation controls (speed, pause), include verbose logging for debugging

# Don't couple simulation timing with real time, don't ignore time delta inconsistencies
# Don't make the loop too complex with seperate functions, also use error handling


# 7 - Execution

if __name__ is "__main__":
    """
    Allow overriding configuration from command line
    """
    if len(sys.argv) > 1:
        HOST = sys.argv[1]
    if len(sys.argv) > 2:
        PORT = int(sys.argv[2])
    
    print(f"Starting BLE fingerprinting simulation with {NUM_MINERS} miners")
    print(f"Grid : {GRID_WIDTH}X{GRID_HEIGHT} with {NUM_BEACONS} BLE beacons")
    print(f"Sending to {HOST}:{PORT} every {SEND_INTERVAL} seconds.")

    run_simulation()
