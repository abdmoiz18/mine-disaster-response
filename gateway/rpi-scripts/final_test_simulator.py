"""
Simulates miner devices sending UDP packets to main_final.py
Run main_final.py first, then run this script. 

Usage: python gateway/rpi-scripts/test_simulator. py
"""
import socket
import json
import time
import random

# Configuration - must match main_final.py
UDP_IP = "127.0.0.1"
UDP_PORT = 5000

# Simulated miners with starting positions (must be passable cells in your maze)
MINERS = {
    "M01": {"x": 2, "y": 3},
    "M02": {"x": 8, "y": 5},
}

def generate_miner_packet(miner_id, position):
    """Generate a realistic miner data packet."""
    return {
        "device_id": miner_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "position": position,  # Simulator provides position directly
        "ble_readings": {
            "B1": round(-50 - random.uniform(0, 30), 1),
            "B2": round(-50 - random.uniform(0, 30), 1),
            "B3": round(-50 - random.uniform(0, 30), 1),
        },
        "imu_data": {
            "accel_x": round(random.uniform(-0.1, 0.1), 3),
            "accel_y": round(random.uniform(-0.1, 0.1), 3),
            "accel_z": round(9.8 + random.uniform(-0.1, 0.1), 3),
        },
        "battery": random.randint(70, 100)
    }

def main():
    sock = socket.socket(socket.AF_INET, socket. SOCK_DGRAM)
    
    print("=" * 50)
    print("MINER SIMULATOR")
    print(f"Sending to {UDP_IP}:{UDP_PORT}")
    print("=" * 50)
    print("\nMake sure main_final.py is running first!")
    print("Press Ctrl+C to stop\n")
    
    packet_count = 0
    
    try:
        while True:
            for miner_id, position in MINERS.items():
                # Generate packet
                packet = generate_miner_packet(miner_id, position)
                message = json.dumps(packet). encode('utf-8')
                
                # Send UDP packet
                sock. sendto(message, (UDP_IP, UDP_PORT))
                packet_count += 1
                
                print(f"[{packet_count}] Sent {miner_id}: pos=({position['x']}, {position['y']})")
            
            # Wait between cycles
            time.sleep(3)
            
    except KeyboardInterrupt:
        print(f"\n\nStopped.  Sent {packet_count} packets total.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
