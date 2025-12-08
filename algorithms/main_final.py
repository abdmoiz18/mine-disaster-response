import serial
import time
import json
import numpy as np
import os
import math
from collections import deque

# ==========================================
# 1. SYSTEM CONFIGURATION
# ==========================================
SERIAL_PORT = '/dev/ttyUSB0'  # CHECK THIS on your Pi (e.g., COM3 on Windows)
BAUD_RATE = 115200
RADIO_MAP_FILE = "radio_map.json"

# Timing
SCAN_TRIGGER_CMD = b'S'       # The signal to wake up ESP32s
COLLECTION_WINDOW = 3.0       # How long Pi listens for data (Sec)
CYCLE_INTERVAL = 10.0         # Total duration of one loop (Sec)

# Logic Constraints
MIN_CONFIDENCE = 0.4          # Don't move if confidence is below this
MOVE_LIMIT = 5                # Max steps to send per cycle
BEACON_IDS = ['B1', 'B2', 'B3'] # Fixed order


def generate_floor_plan():

    H, W = 16, 12
    grid = np.ones((H, W), dtype=int) # 1 = Wall

    # Passages (0)
    grid[1, 1:10] = 0
    grid[7:9, 1:10] = 0
    grid[14, 1:10] = 0
    grid[1:15, 2] = 0
    grid[1:15, 8] = 0
    grid[12:14, 5] = 0 # line
    grid[10:13, 9:11] = 0 # hook
    grid[11, 9] = 1       # hook detail

    # Exits (2)
    grid[0, 7] = 2
    grid[6, 1] = 2
    grid[9, 9] = 2
    grid[15, 7] = 2
    return grid

def create_cartesian_maze(visual_grid):

    H, W = visual_grid.shape
    digitized = {
        'grid_cartesian': np.flipud(visual_grid),
        'dimensions': (W, H), # (x_max, y_max)
        'exits': []
    }

    # Extract exits in Cartesian Coords
    for y in range(H):
        for x in range(W):
            if visual_grid[y, x] == 2:
                digitized['exits'].append((x, H - 1 - y))
    return digitized


def solve_maze_bfs(start_x, start_y, maze_data):

    grid = maze_data['grid_cartesian']
    W, H = maze_data['dimensions']
    exits = maze_data['exits']

    # Safety check: Is start a wall?
    if not (0 <= start_x < W and 0 <= start_y < H): return []
    if grid[start_y, start_x] == 1: return [] # Stuck in wall

    queue = deque([(start_x, start_y)])
    parents = {(start_x, start_y): None}
    target = None

    while queue:
        cx, cy = queue.popleft()

        if (cx, cy) in exits:
            target = (cx, cy)
            break

        # Check neighbors (Up, Down, Left, Right)
        for dx, dy in [(0, 1), (0, -1), (-1, 0), (1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < W and 0 <= ny < H:
                if grid[ny, nx] != 1 and (nx, ny) not in parents:
                    parents[(nx, ny)] = (cx, cy)
                    queue.append((nx, ny))

    if not target: return []

    # Backtrack path
    path = []
    curr = target
    while curr:
        path.append(curr)
        curr = parents[curr]
    return path[::-1] # Reverse to get Start -> End

def path_to_moves(path_coords):
    """Converts coordinates to simple F/L/R moves (Assuming NORTH start)."""
    if len(path_coords) < 2: return []

    moves = []
    # Direction mappings: 0:N, 1:E, 2:S, 3:W
    current_facing = 0

    # We start at index 0, moving to index 1
    for i in range(len(path_coords) - 1):
        cx, cy = path_coords[i]
        nx, ny = path_coords[i+1]

        dx = nx - cx
        dy = ny - cy

        # Determine needed facing
        if dy == 1: needed = 0   # N
        elif dx == 1: needed = 1 # E
        elif dy == -1: needed = 2 # S
        elif dx == -1: needed = 3 # W
        else: needed = current_facing # Should not happen

        # Calculate Turn
        diff = (needed - current_facing) % 4
        if diff == 1: moves.append('R')
        elif diff == 2: moves.extend(['R', 'R'])
        elif diff == 3: moves.append('L')

        # Move Forward
        moves.append('F')
        current_facing = needed

    return moves

class RSSIPreprocessor:

    def process_batch(self, raw_list):
        if not raw_list: return None

        # Extract lists for each beacon
        b_data = {b: [] for b in BEACON_IDS}
        for packet in raw_list:
            if "rssi" in packet and len(packet["rssi"]) == 3:
                for i, b in enumerate(BEACON_IDS):
                    val = packet["rssi"][i]
                    if val > -95: # Filter weak signals
                        b_data[b].append(val)

        # Calculate Averages
        clean_rssi = {}
        for b in BEACON_IDS:
            vals = b_data[b]
            if not vals:
                clean_rssi[b] = -100.0
            else:

                if len(vals) > 4:
                    vals.remove(min(vals))
                    vals.remove(max(vals))
                clean_rssi[b] = round(np.mean(vals), 1)
        return clean_rssi

class FingerprintMatcher:

    def __init__(self, map_file):
        self.radio_map = {}
        if os.path.exists(map_file):
            try:
                with open(map_file, 'r') as f:
                    self.radio_map = json.load(f)
                print(f"[SYSTEM] Radio Map Loaded: {len(self.radio_map)} cells.")
            except:
                print("[ERROR] Radio Map Corrupt.")
        else:
            print("[ERROR] Radio Map NOT FOUND. Localization will fail.")

    def locate(self, rssi_dict):
        best_cell = None
        best_score = float('inf')

        for cell_id, stats in self.radio_map.items():
            dist = 0.0
            valid_beacons = 0

            for b in BEACON_IDS:
                if b in stats:
                    # Euclidean Distance
                    map_mean = stats[b]['mean']
                    curr_val = rssi_dict.get(b, -100.0)
                    if curr_val > -90:
                        diff = curr_val - map_mean
                        dist += diff * diff
                        valid_beacons += 1

            if valid_beacons > 0:
                score = math.sqrt(dist) / valid_beacons
                if score < best_score:
                    best_score = score
                    best_cell = cell_id


        confidence = max(0.0, 1.0 - (best_score / 15.0))

        if best_cell:
            parts = best_cell.split(',')
            return int(parts[0]), int(parts[1]), round(confidence, 2)
        return None, None, 0.0


def listen_and_collect_burst(ser, timeout):
    """Collects all JSON packets from ESP32s."""
    readings = []
    start = time.time()
    ser.reset_input_buffer()

    while (time.time() - start) < timeout:
        if ser.in_waiting:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line.startswith('{'):
                    data = json.loads(line)
                    readings.append(data)
            except:
                pass # Ignore noise
    return readings

def send_command(ser, miner_id, move_list, msg=""):

    payload = {
        "target": miner_id,
        "type": "move",
        "cmd": move_list,
        "msg": msg
    }
    cmd_str = json.dumps(payload) + "\n"
    ser.write(cmd_str.encode('utf-8'))
    print(f"[TX] -> {miner_id}: {move_list}")

def log_to_azure_stub(miner_id, loc, status):
    """Placeholder for Cloud Logging."""
    # In production, use azure.iot.device here
    # print(f"[CLOUD] Uploading {miner_id} status: {status} at {loc}")
    pass

    print("=== NAV HUB STARTING ===")

    # 1. Setup Assets
    visual_grid = generate_floor_plan()
    maze_data = create_cartesian_maze(visual_grid)
    preprocessor = RSSIPreprocessor()
    matcher = FingerprintMatcher(RADIO_MAP_FILE)

    # 2. Setup Serial
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        time.sleep(2)
        print(f"[SYSTEM] Serial Connected: {SERIAL_PORT}")
    except Exception as e:
        print(f"[CRITICAL] Serial Failed: {e}")
        return

    # 3. State Tracking
    # Format: {'M01': {'last_pos': (0,0), 'missed_scans': 0}}
    miner_states = {}

    try:
        while True:
            cycle_start = time.time()
            print(f"\n--- NEW CYCLE (T={time.strftime('%H:%M:%S')}) ---")

            # --- PHASE 1: TRIGGER & COLLECT ---
            print("[1] Triggering Scans...")
            ser.write(SCAN_TRIGGER_CMD) # Send 'S'

            raw_data = listen_and_collect_burst(ser, COLLECTION_WINDOW)
            print(f"    Captured {len(raw_data)} packets.")

            # Group data by Miner ID
            miner_batches = {}
            for pkt in raw_data:
                mid = pkt.get('id', 'Unknown')
                if mid.startswith('M'):
                    if mid not in miner_batches: miner_batches[mid] = []
                    miner_batches[mid].append(pkt)

            # --- PHASE 2: PROCESS & PLAN ---
            for mid, batch in miner_batches.items():
                print(f"[2] Processing {mid}...")

                # A. Clean Signal
                clean_rssi = preprocessor.process_batch(batch)

                # B. Locate
                mx, my, conf = matcher.locate(clean_rssi)

                if mx is None:
                    print(f"    [WARN] Location Unknown.")
                    continue

                print(f"    [LOC] ({mx}, {my}) Conf: {conf}")

                # C. Confidence Gate
                if conf < MIN_CONFIDENCE:
                    print("    [STOP] Low Confidence. Holding.")
                    send_command(ser, mid, [], "Scanning...")
                    continue

                # D. Update State
                miner_states[mid] = {'last_pos': (mx, my)}
                log_to_azure_stub(mid, (mx, my), "ACTIVE")

                # E. Pathfinding
                full_path = solve_maze_bfs(mx, my, maze_data)

                if not full_path:
                    print("    [WARN] No path to exit!")
                    send_command(ser, mid, [], "No Path")
                    continue

                # F. Convert to Moves (Slice Limit)
                all_moves = path_to_moves(full_path)
                next_batch = all_moves[:MOVE_LIMIT]

                # --- PHASE 3: EXECUTE ---
                dist_msg = f"Exit: {len(full_path)}m"
                send_command(ser, mid, next_batch, dist_msg)

            # --- PHASE 4: SLEEP ---
            elapsed = time.time() - cycle_start
            sleep_time = max(0, CYCLE_INTERVAL - elapsed)
            print(f"[4] Sleeping {round(sleep_time, 1)}s for movement...")
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutting Down.")
        ser.close()

if __name__ == "__main__":
    main()
