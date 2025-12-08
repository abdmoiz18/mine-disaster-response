from algorithms.solver_and_orientation import get_navigation_stack

def convert_coordinate_stack_to_move_sequence(coord_stack, start_x, start_y, start_facing='N'):
    if not coord_stack:
        return []

    direction_vectors = {'N': (0, 1), 'E': (1, 0), 'S': (0, -1), 'W': (-1, 0)}
    direction_order = ['N', 'E', 'S', 'W']

    move_sequence = []
    current_x, current_y = start_x, start_y
    current_facing = start_facing

    for target_x, target_y in coord_stack:
        dx = target_x - current_x
        dy = target_y - current_y

        if dx == 0 and dy == 0:
            continue

        if dx > 0:
            needed_facing = 'E'
        elif dx < 0:
            needed_facing = 'W'
        elif dy > 0:
            needed_facing = 'N'
        elif dy < 0:
            needed_facing = 'S'

        current_idx = direction_order.index(current_facing)
        needed_idx = direction_order.index(needed_facing)
        turn_diff = (needed_idx - current_idx) % 4

        if turn_diff == 1:
            move_sequence.append('R')
        elif turn_diff == 2:
            move_sequence.append('R')
            move_sequence.append('R')
        elif turn_diff == 3:
            move_sequence.append('L')

        move_sequence.append('F')

        current_facing = needed_facing
        current_x, current_y = target_x, target_y

    return move_sequence

def get_move_sequence_for_miner(miner_id, start_x, start_y, maze_data):
    coord_stack = get_navigation_stack(miner_id, start_x, start_y, maze_data)
    move_sequence = convert_coordinate_stack_to_move_sequence(coord_stack, start_x, start_y, 'N')
    return move_sequence

def display_move_sequence(miner_id, move_sequence):
    if not move_sequence:
        print(f"Miner {miner_id}: No moves")
        return

    print(f"Miner {miner_id} move sequence ({len(move_sequence)} moves):")
    move_string = ' '.join(move_sequence)
    print(f"  {move_string}")
    print("  F=Forward, L=Left 90°, R=Right 90°")
