"""
Creates a simulated radio map for testing without hardware. 
Run: python algorithms/create_test_radio_map.py
"""
import json
import numpy as np
import os

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "radio_map.json")

# Beacon positions (update to match your planned setup)
BEACON_POSITIONS = {
    "B1": [0, 0],
    "B2": [11, 0],
    "B3": [5, 7]
}

def distance(x, y, beacon_pos):
    return np.sqrt((x - beacon_pos[0])**2 + (y - beacon_pos[1])**2)

def rssi_from_distance(d, tx_power=-50, path_loss=2.5):
    """Log-distance path loss model."""
    if d < 0.5:
        d = 0.5
    return tx_power - 10 * path_loss * np.log10(d)

def get_passable_cells():
    """Get passable cells from your maze layout."""
    # Based on your maze_creation.py
    H, W = 16, 12
    grid = np.ones((H, W), dtype=int)
    
    # Passages
    grid[1, 1:10] = 0
    grid[7:9, 1:10] = 0
    grid[14, 1:10] = 0
    grid[1:15, 2] = 0
    grid[1:15, 8] = 0
    grid[12:14, 5] = 0
    grid[10:13, 9:11] = 0
    grid[11, 9] = 1
    
    # Exits
    grid[0, 7] = 2
    grid[6, 1] = 2
    grid[9, 9] = 2
    grid[15, 7] = 2
    
    # Flip for Cartesian (origin at bottom-left)
    grid_cart = np.flipud(grid)
    
    cells = []
    for y in range(H):
        for x in range(W):
            if grid_cart[y, x] in [0, 2]:  # Passage or exit
                cells. append((x, y))
    
    return cells

def create_radio_map():
    cells = {}
    passable = get_passable_cells()
    
    print(f"Creating radio map for {len(passable)} passable cells...")
    
    for x, y in passable:
        cell_id = f"{x},{y}"
        beacon_stats = {}
        
        for beacon_id, beacon_pos in BEACON_POSITIONS.items():
            d = distance(x, y, beacon_pos)
            mean_rssi = rssi_from_distance(d)
            std_rssi = 2.0 + np.random.uniform(0, 1)
            
            beacon_stats[beacon_id] = {
                "mean": round(float(mean_rssi), 2),
                "std": round(float(std_rssi), 2),
                "samples": 30
            }
        
        cells[cell_id] = {
            "x": x,
            "y": y,
            "beacon_stats": beacon_stats
        }
    
    radio_map = {
        "cells": cells,
        "beacon_positions": BEACON_POSITIONS,
        "grid_resolution": 1.0,
        "coordinate_system": "cartesian",
        "metadata": {
            "type": "simulated",
            "total_cells": len(cells),
            "beacon_ids": ["B1", "B2", "B3"]
        }
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(radio_map, f, indent=2)
    
    print(f"✅ Created radio map: {OUTPUT_FILE}")
    print(f"   Cells: {len(cells)}")
    print(f"   Beacons: B1, B2, B3")

if __name__ == "__main__":
    create_radio_map()
