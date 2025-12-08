# File: collect_rssi.py
# Run this on ESP32 connected to laptop via serial

import time
import csv
from datetime import datetime
import bluetooth  # You'll need to install/use appropriate BLE library

class BLE_Scanner:
    def __init__(self, beacon_macs=None):
        # These MAC addresses should match your physical beacons
        self.beacon_macs = beacon_macs or {
            'B1': 'AA:BB:CC:DD:EE:01',  # Replace with actual B1 MAC
            'B2': 'AA:BB:CC:DD:EE:02',  # Replace with actual B2 MAC
            'B3': 'AA:BB:CC:DD:EE:03',  # Replace with actual B3 MAC
        }
        self.scanner = bluetooth.BLE()
    
    def scan_for_beacons(self, duration_sec=10):
        """Scan for beacons and return RSSI values"""
        print(f"Scanning for {duration_sec} seconds...")
        
        samples = {'B1': [], 'B2': [], 'B3': []}
        start_time = time.time()
        
        while time.time() - start_time < duration_sec:
            # This is pseudocode - actual BLE scanning depends on your library
            # Typically: scanner.scan(duration), then process advertisements
            
            # Simulated scanning for demonstration
            time.sleep(0.1)  # 100ms between scans
            
            # In real code, you'd do:
            # devices = self.scanner.scan(0.1)  # Scan for 100ms
            # for device in devices:
            #     if device.addr in self.beacon_macs.values():
            #         beacon_id = [k for k,v in self.beacon_macs.items() if v == device.addr][0]
            #         samples[beacon_id].append(device.rssi)
            
            # For now, simulate data
            for beacon in ['B1', 'B2', 'B3']:
                # Simulate RSSI with some noise
                base_rssi = -70 + np.random.normal(0, 3)
                samples[beacon].append(base_rssi)
            
            print(".", end="", flush=True)
        
        print("\nScan complete!")
        return samples

def main():
    print("="*50)
    print("ESP32 BLE Data Collection for Radio Map")
    print("="*50)
    
    # Get cell information
    cell_id = input("Enter cell ID (e.g., A1): ").strip().upper()
    x = float(input("Enter approximate X position (meters): "))
    y = float(input("Enter approximate Y position (meters): "))
    
    # Initialize scanner
    scanner = BLE_Scanner()
    
    # Collect data
    print(f"\nCollecting data for cell {cell_id} at ({x}, {y})...")
    samples = scanner.scan_for_beacons(duration_sec=10)
    
    # Calculate statistics
    stats = {}
    for beacon_id, rssi_list in samples.items():
        if rssi_list:
            stats[beacon_id] = {
                'mean': float(np.mean(rssi_list)),
                'std': float(np.std(rssi_list)),
                'min': float(min(rssi_list)),
                'max': float(max(rssi_list)),
                'samples': len(rssi_list)
            }
        else:
            stats[beacon_id] = None
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{cell_id}_data.csv"
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['cell_id', 'x', 'y', 'timestamp', 'beacon', 'rssi'])
        
        for beacon_id, rssi_list in samples.items():
            for rssi in rssi_list:
                writer.writerow([cell_id, x, y, timestamp, beacon_id, rssi])
    
    # Print summary
    print(f"\nSaved {sum(len(v) for v in samples.values())} samples to {filename}")
    print("\nStatistics:")
    for beacon_id, stat in stats.items():
        if stat:
            print(f"  {beacon_id}: mean={stat['mean']:.1f}dBm, std={stat['std']:.1f}, "
                  f"samples={stat['samples']}")
        else:
            print(f"  {beacon_id}: No samples")
    
    # Also save statistics JSON for quick aggregation
    stat_filename = f"{cell_id}_stats.json"
    with open(stat_filename, 'w') as f:
        json.dump({
            'cell_id': cell_id,
            'x': x,
            'y': y,
            'timestamp': timestamp,
            'beacon_stats': stats
        }, f, indent=2)
    
    print(f"\nStatistics saved to {stat_filename}")
    print("="*50)

if __name__ == "__main__":
    main()
