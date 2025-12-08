class MinerStateManager:
    def __init__(self, expected_miner_ids=None):
        """
        Initialize state manager.
        expected_miner_ids: Optional list of expected miner IDs (M01-M05)
        If None, miners will be added dynamically as they are discovered.
        """
        self.miner_states = {}  # Dict: miner_id -> MinerState
        self.expected_miners = expected_miner_ids or []
        self.initialize_expected_miners()

    def initialize_expected_miners(self):
        """Pre-initialize state for expected miners."""
        for miner_id in self.expected_miners:
            self.add_miner(miner_id)

    def add_miner(self, miner_id):
        """Add a new miner with default state."""
        if miner_id not in self.miner_states:
            self.miner_states[miner_id] = {
                'miner_id': miner_id,
                'current_location': None,  # (x, y)
                'previous_location': None,  # (x, y)
                'smoothed_rssi': {},  # beacon_id -> smoothed RSSI value
                'confidence': 0.0,
                'last_update_timestamp': None,
                'movement_history': [],  # List of (x, y, timestamp)
                'status': 'INACTIVE',  # INACTIVE, ACTIVE, ERROR, OFFLINE
                'last_confidence': 0.0,
                'consecutive_low_confidence': 0,
                'estimated_orientation': 'N',  # Track facing direction
                'instruction_queue': [],  # Commands to execute
                'last_instruction_index': 0,
                'cycle_count': 0,
                'total_samples': 0
            }

    def update_miner_location(self, miner_id, new_location, confidence, timestamp):
        """
        Update miner's location with temporal consistency checks.
        new_location: (x, y) tuple
        confidence: 0.0-1.0
        timestamp: current time
        """
        if miner_id not in self.miner_states:
            self.add_miner(miner_id)

        state = self.miner_states[miner_id]

        # Store previous location
        state['previous_location'] = state['current_location']
        state['current_location'] = new_location
        state['confidence'] = confidence
        state['last_update_timestamp'] = timestamp
        state['status'] = 'ACTIVE'
        state['last_confidence'] = confidence
        state['cycle_count'] += 1

        # Update movement history (keep last 10 positions)
        state['movement_history'].append((new_location[0], new_location[1], timestamp))
        if len(state['movement_history']) > 10:
            state['movement_history'].pop(0)

        # Track low confidence streaks
        if confidence < 0.5:
            state['consecutive_low_confidence'] += 1
        else:
            state['consecutive_low_confidence'] = 0

        # Mark as ERROR if too many low confidence readings
        if state['consecutive_low_confidence'] >= 3:
            state['status'] = 'ERROR'

    def update_smoothed_rssi(self, miner_id, beacon_id, smoothed_value):
        """Update smoothed RSSI value for a specific beacon."""
        if miner_id not in self.miner_states:
            self.add_miner(miner_id)

        self.miner_states[miner_id]['smoothed_rssi'][beacon_id] = smoothed_value

    def update_orientation(self, miner_id, new_orientation):
        """Update miner's estimated facing direction."""
        if miner_id in self.miner_states:
            self.miner_states[miner_id]['estimated_orientation'] = new_orientation

    def update_instruction_queue(self, miner_id, instruction_queue):
        """Set new instruction queue for miner."""
        if miner_id in self.miner_states:
            self.miner_states[miner_id]['instruction_queue'] = instruction_queue
            self.miner_states[miner_id]['last_instruction_index'] = 0

    def increment_instruction_index(self, miner_id):
        """Move to next instruction in queue."""
        if miner_id in self.miner_states:
            state = self.miner_states[miner_id]
            if state['last_instruction_index'] < len(state['instruction_queue']) - 1:
                state['last_instruction_index'] += 1

    def get_current_instruction(self, miner_id):
        """Get current instruction for miner."""
        if miner_id in self.miner_states:
            state = self.miner_states[miner_id]
            if state['instruction_queue']:
                idx = state['last_instruction_index']
                if idx < len(state['instruction_queue']):
                    return state['instruction_queue'][idx]
        return None

    def get_miner_state(self, miner_id):
        """Get complete state for a miner."""
        return self.miner_states.get(miner_id)

    def get_active_miners(self):
        """Get list of miners with ACTIVE status."""
        active = []
        for miner_id, state in self.miner_states.items():
            if state['status'] == 'ACTIVE':
                active.append(miner_id)
        return active

    def get_inactive_miners(self):
        """Get list of miners with INACTIVE status."""
        inactive = []
        for miner_id, state in self.miner_states.items():
            if state['status'] == 'INACTIVE':
                inactive.append(miner_id)
        return inactive

    def reset_miner(self, miner_id):
        """Reset miner to initial state but keep ID."""
        if miner_id in self.miner_states:
            self.miner_states[miner_id].update({
                'current_location': None,
                'previous_location': None,
                'confidence': 0.0,
                'status': 'INACTIVE',
                'instruction_queue': [],
                'last_instruction_index': 0,
                'consecutive_low_confidence': 0
            })

    def calculate_movement_vector(self, miner_id):
        """
        Calculate movement vector from previous to current location.
        Returns (dx, dy) or None if insufficient data.
        """
        state = self.miner_states.get(miner_id)
        if not state:
            return None

        current = state['current_location']
        previous = state['previous_location']

        if current is None or previous is None:
            return None

        dx = current[0] - previous[0]
        dy = current[1] - previous[1]
        return (dx, dy)

    def get_all_miners_data_for_azure(self):
        """
        Format all miner data for Azure batch transmission.
        Returns list of miner data dictionaries.
        """
        azure_data = []
        for miner_id, state in self.miner_states.items():
            if state['current_location'] is not None and state['status'] == 'ACTIVE':
                miner_data = {
                    'id': miner_id,
                    'estimated_location': {
                        'x': state['current_location'][0],
                        'y': state['current_location'][1]
                    },
                    'confidence': state['confidence'],
                    'status': state['status'],
                    'last_update': state['last_update_timestamp']
                }
                azure_data.append(miner_data)
        return azure_data

    def mark_miner_offline(self, miner_id):
        """Mark miner as offline (no recent updates)."""
        if miner_id in self.miner_states:
            self.miner_states[miner_id]['status'] = 'OFFLINE'

    def get_location_history(self, miner_id, n_points=5):
        """Get last n location points for a miner."""
        state = self.miner_states.get(miner_id)
        if not state or not state['movement_history']:
            return []

        return state['movement_history'][-n_points:]

    def calculate_average_confidence(self):
        """Calculate average confidence across all active miners."""
        active = self.get_active_miners()
        if not active:
            return 0.0

        total = 0.0
        for miner_id in active:
            state = self.miner_states[miner_id]
            total += state['confidence']

        return total / len(active)

    def get_smoothed_rssi_vector(self, miner_id, beacon_ids):
        """
        Get smoothed RSSI values for specific beacons.
        Returns list of RSSI values in same order as beacon_ids.
        Missing values replaced with -100.
        """
        state = self.miner_states.get(miner_id)
        if not state:
            return [-100] * len(beacon_ids)

        rssi_vector = []
        for beacon_id in beacon_ids:
            rssi_vector.append(state['smoothed_rssi'].get(beacon_id, -100))

        return rssi_vector
