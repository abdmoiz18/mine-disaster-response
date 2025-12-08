import serial
import time
import json
import numpy as np
import os

# --- CONFIGURATION ---
SERIAL_PORT = 'COM3'  # Change to your ESP32 Port (e.g., '/dev/ttyUSB0' on Linux/Mac)
BAUD_RATE = 115200
SCAN_TRIGGER_CMD = b'S'  # The signal to start the burst
BURST_TIMEOUT = 3.0      # How long to listen for the burst (seconds)
OUTPUT_FILE = "radio_map.json"

def listen_and_parse_json_burst(ser, timeout=3.0):

    valid_readings = []
    start_time = time.time()

    print(f"   Listening for {timeout} seconds...")

    # Clear buffer before starting to avoid old garbage data
    ser.reset_input_buffer()

    while (time.time() - start_time) < timeout:
        if ser.in_waiting > 0:
            try:

                line = ser.readline().decode('utf-8').strip()


                if line:
                    data = json.loads(line)


                    if "rssi" in data and len(data["rssi"]) == 3:
                        valid_readings.append(data)

                        print(".", end="", flush=True)
            except json.JSONDecodeError:
                pass  # Ignore garbage lines
            except Exception as e:
                print(f"\n   Error reading line: {e}")

    print(f"\n   Captured {len(valid_readings)} valid samples.")
    return valid_readings

def calculate_cell_stats(readings):

    if not readings:
        return None

    # Arrays to hold all samples for B1, B2, B3
    b1_samples = []
    b2_samples = []
    b3_samples = []

    for r in readings:
        rssi_list = r["rssi"]
        b1_samples.append(rssi_list[0])
        b2_samples.append(rssi_list[1])
        b3_samples.append(rssi_list[2])

    # Helper to calculate stats safely
    def get_stats(samples):
        # Remove simple outliers (optional safety check)
        clean_samples = [x for x in samples if x < -10 and x > -100]

        if not clean_samples:
            return {"mean": -100.0, "std": 0.0}

        return {
            "mean": round(float(np.mean(clean_samples)), 2),
            "std": round(float(np.std(clean_samples)), 2)
        }

    return {
        "B1": get_stats(b1_samples),
        "B2": get_stats(b2_samples),
        "B3": get_stats(b3_samples)
    }

def main():
    print("=== INDOOR NAVIGATION CALIBRATION TOOL ===")
    print(f"Connecting to {SERIAL_PORT}...")

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        time.sleep(2)  # Wait for connection to settle
        print("Connected.")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # Load existing map if it exists (so you can pause/resume)
    radio_map = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as f:
                radio_map = json.load(f)
            print(f"Loaded existing map with {len(radio_map)} cells.")
        except:
            print("Starting new radio map.")

    while True:
        print("\n----------------------------------------")
        user_input = input("Enter Grid Coordinates 'X,Y' (or 'q' to save & quit): ").strip()

        if user_input.lower() == 'q':
            break

        # Basic format validation
        try:
            x_str, y_str = user_input.split(',')
            cell_id = f"{x_str.strip()},{y_str.strip()}" # Store as string "2,3"
        except ValueError:
            print("Invalid format. Please use 'X,Y' (e.g., 2,3)")
            continue

        print(f"\n-> PREPARE: Walk to Cell ({cell_id}).")
        print("-> ACTION: When you press ENTER, rotate slowly for 2 seconds.")
        input("Press ENTER to Trigger Scan...")

        # 1. Send Trigger
        print(">>> TRIGGER SENT")
        ser.write(SCAN_TRIGGER_CMD)

        # 2. Listen for Burst
        raw_data = listen_and_parse_json_burst(ser, timeout=BURST_TIMEOUT)

        # 3. Process Data
        if len(raw_data) < 10:
            print(f"WARNING: Low sample count ({len(raw_data)}). Retry this cell?")
            retry = input("Retry? (y/n): ")
            if retry.lower() == 'y':
                continue

        stats = calculate_cell_stats(raw_data)

        # 4. Save to Memory
        radio_map[cell_id] = stats
        print(f"SUCCESS: Cell ({cell_id}) saved.")
        print(f"   Stats: {stats}")

    # Final Save
    print(f"\nSaving {len(radio_map)} cells to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(radio_map, f, indent=4)
    print("Done.")
    ser.close()

if __name__ == "__main__":
    main()
