# This script is for testing the full algorithm pipeline.
# It imports the library functions from the 'algorithms' folder and executes them.

from algorithms.maze_creation import generate_floor_plan, create_digitized_maze_data_cartesian
from algorithms.solver import get_navigation_stack
from algorithms.navigation import get_move_sequence_for_miner, display_move_sequence

def main_test():
    """
    Runs an end-to-end test of the navigation system.
    """
    print("--- Initializing Navigation Test ---")
    
    # 1. Create the map data that the algorithms will use
    visual_maze_grid = generate_floor_plan()
    maze_data = create_digitized_maze_data_cartesian(visual_maze_grid)
    
    # 2. Define the test scenario
    miner_id = "M01"
    start_x, start_y = 2, 3  # Cartesian coordinates (bottom-left origin)
    
    print(f"\nScenario: Find path for Miner '{miner_id}' from starting point (x={start_x}, y={start_y})")
    
    # 3. Run the core logic
    # This function will call the solver and then the move sequence converter
    move_sequence = get_move_sequence_for_miner(miner_id, start_x, start_y, maze_data)
    
    # 4. Display the final, user-friendly result
    print("\n--- Test Result ---")
    display_move_sequence(miner_id, move_sequence)
    print("--------------------")

if __name__ == "__main__":
    # This code runs when you execute `python run_test.py` in your terminal
    main_test()
