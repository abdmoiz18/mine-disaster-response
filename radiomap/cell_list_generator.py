import json
import numpy as np
import os
from datetime import datetime

def generate_maze_grid():
    """Recreate the original 16x12 maze grid"""
    H, W = 16, 12
    grid = np.ones((H, W), dtype=int)
    
    # Passages (0) - from original maze
    grid[1, 1:10] = 0
    grid[7:9, 1:10] = 0
    grid[14, 1:10] = 0
    grid[1:15, 2] = 0
    grid[1:15, 8] = 0
    grid[12:14, 5] = 0
    grid[10:13, 9:11] = 0
    
    # Walls (1) are already set
    
    # Exits (2)
    grid[0, 7] = 2
    grid[6, 1] = 2
    grid[9, 9] = 2
    grid[15, 7] = 2
    
    return grid

def get_passable_cells_for_region(y_start=0, y_end=7):
    """
    Get all walkable cells in y range 0-7.
    Returns list of (cell_id, x, y, is_exit)
    """
    grid = generate_maze_grid()
    cells = []
    
    # Define beacon positions (from your Stage 2 setup)
    # You might need to adjust these based on actual placement
    beacon_positions = {
        'B1': (0, 0),    # Bottom-left corner
        'B2': (11, 0),   # Bottom-right corner  
        'B3': (5, 7)     # Top-center of your region
    }
    
    # For y=0 to 7 (inclusive)
    for y in range(y_start, y_end + 1):
        for x in range(12):  # x=0 to 11
            # Only include passable cells (0) and exits (2)
            if grid[y, x] in [0, 2]:
                # Convert to cell ID: A1, A2, ... B1, B2, ...
                row_letter = chr(65 + y)  # A for y=0, B for y=1, etc.
                col_number = x + 1        # 1-indexed columns
                cell_id = f"{row_letter}{col_number}"
                
                cells.append({
                    'cell_id': cell_id,
                    'grid_x': x,
                    'grid_y': y,
                    'is_exit': (grid[y, x] == 2),
                    'physical_center_m': (x + 0.5, y + 0.5),  # Assuming 1m spacing
                    'beacon_distances': {
                        'B1': np.sqrt((x - beacon_positions['B1'][0])**2 + (y - beacon_positions['B1'][1])**2),
                        'B2': np.sqrt((x - beacon_positions['B2'][0])**2 + (y - beacon_positions['B2'][1])**2),
                        'B3': np.sqrt((x - beacon_positions['B3'][0])**2 + (y - beacon_positions['B3'][1])**2)
                    }
                })
    
    return cells, beacon_positions

def generate_field_collection_sheet(cells, max_cells=8):
    """
    Create a practical field collection sheet.
    Selects the most strategically important cells.
    """
    # Prioritize: exits first, then cells near beacons, then others
    exit_cells = [c for c in cells if c['is_exit']]
    non_exit_cells = [c for c in cells if not c['is_exit']]
    
    # Sort non-exit cells by beacon coverage (closest to any beacon)
    non_exit_cells.sort(key=lambda c: min(c['beacon_distances'].values()))
    
    # Select cells for MVP
    selected = exit_cells[:2] if len(exit_cells) >= 2 else exit_cells
    remaining = max_cells - len(selected)
    selected.extend(non_exit_cells[:remaining])
    
    print("\n" + "="*60)
    print(f"FIELD COLLECTION SHEET - MVP (Max {max_cells} cells)")
    print("="*60)
    
    for i, cell in enumerate(selected, 1):
        print(f"\n{i}. CELL {cell['cell_id']}")
        print(f"   Grid: ({cell['grid_x']}, {cell['grid_y']})")
        print(f"   Physical Position: {cell['physical_center_m'][0]:.1f}m, {cell['physical_center_m'][1]:.1f}m")
        print(f"   Type: {'EXIT' if cell['is_exit'] else 'Passage'}")
        print(f"   Distances to beacons: B1={cell['beacon_distances']['B1']:.1f}m, "
              f"B2={cell['beacon_distances']['B2']:.1f}m, "
              f"B3={cell['beacon_distances']['B3']:.1f}m")
        print(f"   Instructions:")
        print(f"     1. Stand at approximate center of cell {cell['cell_id']}")
        print(f"     2. Hold ESP32 at waist height")
        print(f"     3. Run collection script for 10 seconds")
        print(f"     4. Record filename: {cell['cell_id']}_data.csv")
    
    print("\n" + "="*60)
    print("QUICK START:")
    print("1. Start with cells near exits (priority)")
    print("2. Then collect cells near beacons for better signal")
    print("3. 10 seconds per cell is enough for MVP")
    print("4. Save each as cellname_data.csv")
    print("="*60)
    
    return selected

if __name__ == "__main__":
    # Generate cell list for y=0 to 7
    all_cells, beacon_pos = get_passable_cells_for_region(0, 7)
    
    print(f"Found {len(all_cells)} passable cells in y=0 to 7 region")
    
    # For MVP, select only 8 cells to measure
    mvp_cells = generate_field_collection_sheet(all_cells, max_cells=8)
    
    # Save the MVP cells to a JSON file for reference
    with open('mvp_cells_to_collect.json', 'w') as f:
        json.dump({
            'beacon_positions': beacon_pos,
            'selected_cells': mvp_cells,
            'total_available_cells': len(all_cells),
            'generated_at': datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\nSaved MVP cell list to 'mvp_cells_to_collect.json'")
