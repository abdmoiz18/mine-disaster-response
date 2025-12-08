"""
Converts existing radio_map.json to the format expected by FingerprintMatcher. 
Run once: python algorithms/convert_radio_map.py
"""
import json
import os

# Configuration
RADIO_MAP_FILE = os.path.join(os.path.dirname(__file__), "radio_map.json")
BACKUP_FILE = os. path.join(os.path.dirname(__file__), "radio_map_backup.json")

BEACON_POSITIONS = {
    "B1": [0, 0],
    "B2": [11, 0],
    "B3": [5, 7]
}

def convert():
    if not os.path.exists(RADIO_MAP_FILE):
        print(f"❌ {RADIO_MAP_FILE} not found")
        return

    with open(RADIO_MAP_FILE, 'r') as f:
        data = json.load(f)

    # Already in correct format? 
    if "cells" in data and "beacon_positions" in data:
        print("✅ Radio map already in correct format")
        return

    # Backup original
    with open(BACKUP_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"📦 Backup saved to {BACKUP_FILE}")

    # Convert
    cells = {}
    for cell_id, beacon_stats in data. items():
        try:
            x, y = map(int, cell_id. split(','))
            cells[cell_id] = {"x": x, "y": y, "beacon_stats": beacon_stats}
        except:
            continue

    new_format = {
        "cells": cells,
        "beacon_positions": BEACON_POSITIONS,
        "grid_resolution": 1.0,
        "coordinate_system": "cartesian"
    }

    with open(RADIO_MAP_FILE, 'w') as f:
        json.dump(new_format, f, indent=4)

    print(f"✅ Converted {len(cells)} cells in {RADIO_MAP_FILE}")

if __name__ == "__main__":
    convert()
