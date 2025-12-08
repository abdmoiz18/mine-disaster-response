import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np

def generate_floor_plan():
    # 1. Setup the Grid Dimensions
    H, W = 16, 12

    # Create a grid of ones (1 = Wall) to start, then carve out passages
    grid = np.ones((H, W), dtype=int)

    # --- DEFINING THE MAP ELEMENTS --- (now carving passages with 0)
    # Horizontal Passages
    grid[1, 1:10] = 0
    grid[7:9, 1:10] = 0
    grid[14, 1:10] = 0

    # Vertical Passages
    grid[1:15, 2] = 0
    grid[1:15, 8] = 0

    # Details (carving out specific passages)
    grid[12:14, 5] = 0 #line (passage)
    grid[10:13, 9:11] = 0 #hook (passage)
    grid[11, 9] = 1 # This was originally 0 (passage) but is specified as part of the 'hook' details. If it should be a wall, keep it 1. If it was intended as a passage, change to 0.

    # Exits (2 remain 2)
    grid[0, 7] = 2
    grid[6, 1] = 2
    grid[9, 9] = 2
    grid[15, 7] = 2

    return grid

def visualize_map(grid):
    # Create a custom color map:
    # 0=White (Passage), 1=Blue (Wall), 2=Red (Exit)
    cmap = colors.ListedColormap(['white', 'blue', '#990000'])
    bounds = [-0.5, 0.5, 1.5, 2.5]
    norm = colors.BoundaryNorm(bounds, cmap.N)

    fig, ax = plt.subplots(figsize=(8, 12))

    # Plot the grid
    im = ax.imshow(grid, cmap=cmap, norm=norm)

    # --- BEAUTIFY THE GRID ---
    # Major ticks at integers
    ax.set_xticks(np.arange(0, grid.shape[1], 1))
    ax.set_yticks(np.arange(0, grid.shape[0], 1))

    # Minor ticks at .5 intervals (for the grid lines)
    ax.set_xticks(np.arange(-0.5, grid.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, grid.shape[0], 1), minor=True)

    # Draw grid only on minor ticks (the edges)
    ax.grid(which='minor', color='lightgray', linestyle='-', linewidth=1)
    ax.grid(which='major', color='r', linestyle='', linewidth=0)

    # Labels
    ax.set_xlabel("X Coordinates")
    ax.set_ylabel("Y Coordinates")
    ax.set_title("Corrected Floor Plan Grid")

    ax.tick_params(which='minor', size=0)
    ax.set_aspect('equal')

    plt.tight_layout()
    plt.show()

def create_digitized_maze_data(visual_grid):

    H, W = visual_grid.shape


    digitized = {
        'grid': visual_grid.copy(),
        'dimensions': (H, W),
        'coordinate_system': 'grid[y, x] where y=row (0-24), x=col (0-16)',

        # Extract all exits (value == 2)
        'exits': [],

        # Extract all walls (value == 1)
        'walls': [],

        # Extract all walkable passages (value == 0)
        'passages': []
    }

    # Scan the grid and categorize each cell
    for y in range(H):
        for x in range(W):
            value = visual_grid[y, x]
            coord = (x, y)  # (x, y) Cartesian format

            if value == 2:  # Exit
                digitized['exits'].append(coord)
            elif value == 1:  # Wall
                digitized['walls'].append(coord)
            else:  # Passage (value == 0)
                digitized['passages'].append(coord)

    return digitized

def print_maze_summary(digitized_data):
    """Print a clear summary of the digitized maze data."""
    print("\n" + "="*60)
    print("DIGITIZED MAZE DATA SUMMARY")
    print("="*60)

    H, W = digitized_data['dimensions']
    print(f"Dimensions: {H} rows (y: 0-{H-1}), {W} columns (x: 0-{W-1})")
    print(f"Coordinate System: {digitized_data['coordinate_system']}")

    print(f"\nExits ({len(digitized_data['exits'])} locations):")
    for x, y in digitized_data['exits']:
        print(f"  (x={x:2d}, y={y:2d}) - Grid[{y:2d}, {x:2d}]")

    print(f"\nWalls: {len(digitized_data['walls'])} cells")
    print(f"Passages: {len(digitized_data['passages'])} cells")

    # Print grid with coordinates for reference
    print("\nGrid Reference (First 5 rows):")
    print("y\\x ", end="")
    for x in range(min(10, W)):
        print(f"{x:3d}", end="")
    print("...")

    for y in range(min(5, H)):
        print(f"{y:2d}: ", end="")
        for x in range(min(10, W)):
            value = digitized_data['grid'][y, x]
            if value == 0:
                print("  .", end="")
            elif value == 1:
                print("  #", end="")
            else:
                print("  E", end="")
        print("...")

    print("="*60)

if __name__ == "__main__":
    # Generate the visual maze (original functionality)
    visual_maze_grid = generate_floor_plan()

    # Show the visualization (original functionality)
    visualize_map(visual_maze_grid)

    print("Original Map Shape:", visual_maze_grid.shape)

    # Create digitized version for pathfinding
    digitized_maze = create_digitized_maze_data(visual_maze_grid)

    # Print summary of digitized data
    print_maze_summary(digitized_maze)


    print("\nExample access to digitized data:")
    print(f"First exit at: {digitized_maze['exits'][0]}")
    print(f"Is (x=5, y=5) walkable? {digitized_maze['grid'][5, 5] == 0}")
    print(f"Total walkable cells: {len(digitized_maze['passages'])}")
