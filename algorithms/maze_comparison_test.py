import numpy as np

def print_maze_detailed(grid, title="Maze Grid"):
    """
    Prints a text-based visualization of the maze grid with 'W' for Wall, 'P' for Passage, and 'E' for Exit.
    Args:
        grid (np.ndarray): The maze grid, where 0=passage, 1=wall, 2=exit.
        title (str): Title for the printed maze.
    """
    height, width = grid.shape
    output_lines = []

    output_lines.append(f"\n{title} (Y=Rows, X=Columns):\n")

    # X-axis header (horizontal coordinates / columns)
    x_axis_header = "X:" + " ".join([f"{i:2d}" for i in range(width)])
    output_lines.append(x_axis_header)
    output_lines.append("  " + "--" * width)

    for y in range(height):
        row_str = f"Y:{y:2d}|"
        for x in range(width):
            cell_val = grid[y, x]
            if cell_val == 1:
                row_str += " W"
            elif cell_val == 2:
                row_str += " E"
            else:
                row_str += " P"
        output_lines.append(row_str)

    print("\n".join(output_lines))

# --- Original generate_floor_plan function from BWTuZ-XtH14Y --- (added for definition)
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
# --- End of original generate_floor_plan function ---

# Get the original maze grid by calling the function
maze_original = generate_floor_plan()

# --- Copied generate_floor_plan from cell mAujiGrixvut and renamed ---
def generate_floor_plan_from_main_loop():
    """Hardcoded 16x12 grid from your Colab design."""
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
# --- End of copied function ---

# Generate the maze from the copied functionimport numpy as np

def print_maze_detailed(grid, title="Maze Grid"):
    """
    Prints a text-based visualization of the maze grid with 'W' for Wall, 'P' for Passage, and 'E' for Exit.
    Args:
        grid (np.ndarray): The maze grid, where 0=passage, 1=wall, 2=exit.
        title (str): Title for the printed maze.
    """
    height, width = grid.shape
    output_lines = []

    output_lines.append(f"\n{title} (Y=Rows, X=Columns):\n")

    # X-axis header (horizontal coordinates / columns)
    x_axis_header = "X:" + " ".join([f"{i:2d}" for i in range(width)])
    output_lines.append(x_axis_header)
    output_lines.append("  " + "--" * width)

    for y in range(height):
        row_str = f"Y:{y:2d}|"
        for x in range(width):
            cell_val = grid[y, x]
            if cell_val == 1:
                row_str += " W"
            elif cell_val == 2:
                row_str += " E"
            else:
                row_str += " P"
        output_lines.append(row_str)

    print("\n".join(output_lines))

# --- Original generate_floor_plan function from BWTuZ-XtH14Y --- (added for definition)
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
# --- End of original generate_floor_plan function ---

# Get the original maze grid by calling the function
maze_original = generate_floor_plan()

# --- Copied generate_floor_plan from cell mAujiGrixvut and renamed ---
def generate_floor_plan_from_main_loop():
    """Hardcoded 16x12 grid from your Colab design."""
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
# --- End of copied function ---

# Generate the maze from the copied function
maze_from_main_loop = generate_floor_plan_from_main_loop()

# Display both mazes for comparison
print_maze_detailed(maze_original, "Original Maze Grid (from generate_floor_plan)")
print_maze_detailed(maze_from_main_loop, "Maze Grid (from generate_floor_plan_from_main_loop)")
maze_from_main_loop = generate_floor_plan_from_main_loop()

# Display both mazes for comparison
print_maze_detailed(maze_original, "Original Maze Grid (from generate_floor_plan)")
print_maze_detailed(maze_from_main_loop, "Maze Grid (from generate_floor_plan_from_main_loop)")
