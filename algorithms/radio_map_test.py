import time
import json
import numpy as np
import os
import random

# --- MOCK CONFIGURATION ---
# No Serial Port needed for testing
OUTPUT_FILE = "radio_map_TEST.json"

def generate_fake_burst_data():
    """
    Simulates what the ESP32 WOULD send if it were connected.
    Generates 30 samples with slight random variations.
    """
    fake_readings = []

    # Simulate a "base" signal strength for this fake cell
    base_b1 = random.uniform(-50, -80)
    base_b2 = random.uniform(-50, -80)
    base_b3 = random.uniform(-50, -80)

    print("   [SIMULATION] Receiving data from virtual ESP32...", end="")

    # Generate 30 fake packets
    for _ in range(30):
        fake_packet = {
            "id": "M01",
            "rssi": [
                round(base_b1 + random.uniform(-2, 2), 1), # Add noise
                round(base_b2 + random.uniform(-2, 2), 1),
                round(base_b3 + random.uniform(-2, 2), 1)
            ]
        }
        fake_readings.append(fake_packet)
        time.sleep(0.05) # Simulate data streaming speed
        print(".", end="", flush=True)

    print(f"\n   [SIMULATION] Captured {len(fake_readings)} fake samples.")
    return fake_readings

def calculate_cell_stats(readings):
    """
    (Same logic as real code) Converts raw list into stats.
    """
    if not readings: return None

    b1 = [r["rssi"][0] for r in readings]
    b2 = [r["rssi"][1] for r in readings]
    b3 = [r["rssi"][2] for r in readings]

    def get_stats(samples):
        return {
            "mean": round(float(np.mean(samples)), 2),
            "std": round(float(np.std(samples)), 2)
        }

    return {
        "B1": get_stats(b1),
        "B2": get_stats(b2),
        "B3": get_stats(b3)
    }

def main():
    print("=== CALIBRATION SOFTWARE TEST (NO HARDWARE) ===")

    # Load existing map
    radio_map = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as f:
                radio_map = json.load(f)
            print(f"Loaded existing test map with {len(radio_map)} cells.")
        except:
            print("Starting new test map.")

    while True:
        print("\n----------------------------------------")
        user_input = input("Enter Grid Coordinates 'X,Y' (or 'q' to quit): ").strip()

        if user_input.lower() == 'q':
            break

        try:
            x_str, y_str = user_input.split(',')
            cell_id = f"{x_str.strip()},{y_str.strip()}"
        except ValueError:
            print("Invalid format.")
            continue

        print(f"\n-> [TEST] ({cell_id}).")
        input("Press ENTER to Simulate Scan...")

        # 1. Trigger (Simulated)
        print(" TRIGGER SENT (Simulated)")

        # 2. Listen (Simulated)
        raw_data = generate_fake_burst_data()

        # 3. Process
        stats = calculate_cell_stats(raw_data)

        # 4. Save
        radio_map[cell_id] = stats
        print(f"SUCCESS: Cell ({cell_id}) saved.")
        print(f"   Stats: {stats}")

    # Final Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(radio_map, f, indent=4)
    print(f"\nSaved test data to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()