import numpy as np
from collections import deque
import heapq

def solve_maze_to_nearest_exit(start_x, start_y, maze_data):
    grid = maze_data['grid']
    exits = maze_data['exits']

    H, W = maze_data['dimensions']

    if grid[start_y, start_x] == 1:
        return []

    distance = np.full((H, W), -1, dtype=int)
    parent_x = np.full((H, W), -1, dtype=int)
    parent_y = np.full((H, W), -1, dtype=int)

    queue = deque()
    queue.append((start_x, start_y))
    distance[start_y, start_x] = 0

    target_exit = None

    while queue:
        cx, cy = queue.popleft()

        if (cx, cy) in exits:
            target_exit = (cx, cy)
            break

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = cx + dx, cy + dy

            if 0 <= nx < W and 0 <= ny < H:
                if grid[ny, nx] != 1 and distance[ny, nx] == -1:
                    distance[ny, nx] = distance[cy, cx] + 1
                    parent_x[ny, nx] = cx
                    parent_y[ny, nx] = cy
                    queue.append((nx, ny))

    if target_exit is None:
        return []

    path_coordinates = []
    cx, cy = target_exit

    while not (cx == start_x and cy == start_y):
        path_coordinates.append((cx, cy))
        px = parent_x[cy, cx]
        py = parent_y[cy, cx]
        cx, cy = px, py

    path_coordinates.reverse()
    return path_coordinates

def solve_maze_to_nearest_exit_cartesian(start_x, start_y, maze_data):
    """
    Solves the maze using a Cartesian grid where (0,0) is at the bottom-left.
    This is the primary solver for the system.
    """
    # This code is from your new `solve_maze_to_nearest_exit_cartesian`
    grid_cart = maze_data['grid_cartesian']
    exits = maze_data['exits']
    W, H = maze_data['dimensions']

    # This is a much safer way to check if the start is a wall.
    if grid_cart[start_y, start_x] == 1:
        print(f"Error: Start position ({start_x}, {start_y}) is a wall.")
        return []

def get_navigation_stack(miner_id, current_x, current_y, maze_data):
    path = solve_maze_to_nearest_exit(current_x, current_y, maze_data)

    if not path:
        return []

    return path

def display_navigation_stack(miner_id, stack):
    if not stack:
        print(f"Miner {miner_id}: No path to exit")
        return

    print(f"Miner {miner_id} navigation stack ({len(stack)} steps):")
    for i, (x, y) in enumerate(stack, 1):
        print(f"  Step {i:2d}: Move to (x={x}, y={y})")
