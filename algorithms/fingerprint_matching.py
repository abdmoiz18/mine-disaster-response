import numpy as np
import math
import json
from scipy.stats import norm

class FingerprintMatcher:
    def __init__(self, radio_map_path, confidence_threshold=0.7):
        """
        Production fingerprint matcher for single miner localization.

        Parameters:
        - radio_map_path: Path to JSON radio map file
        - confidence_threshold: Minimum confidence to accept location (0.0-1.0)
        """
        self.radio_map = self._load_radio_map(radio_map_path)
        self.confidence_threshold = confidence_threshold
        self.beacon_ids = ['B1', 'B2', 'B3']

    def _load_radio_map(self, path):
        """Load and validate radio map from JSON."""
        with open(path, 'r') as f:
            radio_map = json.load(f)

        # Validate structure
        required_keys = ['cells', 'beacon_positions', 'grid_resolution', 'coordinate_system']
        for key in required_keys:
            if key not in radio_map:
                raise ValueError(f"Radio map missing required key: {key}")

        return radio_map

    def _gaussian_pdf(self, x, mean, std):
        """Calculate Gaussian probability density."""
        if std <= 0:
            return 0.0
        return (1.0 / (std * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mean) / std) ** 2)

    def _calculate_cell_probability(self, rssi_vector, cell_data):
        """
        Calculate probability that RSSI vector came from this cell using Naive Bayes.
        """
        probability = 1.0

        for beacon_id in self.beacon_ids:
            rssi_value = rssi_vector.get(beacon_id, -100.0)

            # Handle missing beacon (-100 indicates not detected)
            if rssi_value == -100.0:
                # Use low probability for missing beacon
                probability *= 0.01
                continue

            # Get beacon statistics for this cell
            beacon_stats = cell_data.get('beacon_stats', {}).get(beacon_id)
            if not beacon_stats:
                # Beacon not in radio map for this cell
                probability *= 0.01
                continue

            mean = beacon_stats.get('mean')
            std = beacon_stats.get('std')

            if mean is None or std is None or std <= 0:
                probability *= 0.01
                continue

            # Calculate Gaussian probability
            beacon_prob = self._gaussian_pdf(rssi_value, mean, std)

            # Avoid zero probability
            beacon_prob = max(beacon_prob, 1e-10)
            probability *= beacon_prob

        return probability

    def locate_miner(self, processed_rssi, miner_id=None):
        """
        Main localization function for single miner.

        Parameters:
        - processed_rssi: Dict from RSSIPreprocessor {'B1': -65.0, 'B2': -71.5, 'B3': -68.2}
        - miner_id: Optional miner ID for logging

        Returns:
        Dict with location estimate and confidence metrics.
        """
        # Validate input
        if not processed_rssi or not isinstance(processed_rssi, dict):
            return self._error_result("Invalid RSSI input")

        # Check if we have any valid beacon readings
        valid_beacons = [b for b in self.beacon_ids if processed_rssi.get(b, -100.0) > -100.0]
        if len(valid_beacons) < 2:
            return self._error_result(f"Insufficient beacons: {len(valid_beacons)}")

        # Initialize tracking
        cell_probabilities = []
        cell_data_list = []

        # Calculate probability for each cell
        for cell_id, cell_data in self.radio_map['cells'].items():
            probability = self._calculate_cell_probability(processed_rssi, cell_data)

            cell_probabilities.append(probability)
            cell_data_list.append({
                'cell_id': cell_id,
                'x': cell_data['x'],
                'y': cell_data['y'],
                'probability': probability
            })

        # Handle case where all probabilities are zero
        total_probability = sum(cell_probabilities)
        if total_probability <= 0:
            return self._error_result("No matching cells found")

        # Normalize probabilities
        for cell_info in cell_data_list:
            cell_info['normalized_prob'] = cell_info['probability'] / total_probability

        # Sort by probability (descending)
        cell_data_list.sort(key=lambda x: x['normalized_prob'], reverse=True)

        # Get best match
        best_cell = cell_data_list[0]
        best_prob = best_cell['normalized_prob']

        # Calculate confidence metrics
        confidence_score = best_prob

        # Calculate discrimination ratio (best vs second best)
        if len(cell_data_list) > 1:
            second_best_prob = cell_data_list[1]['normalized_prob']
            discrimination_ratio = best_prob / second_best_prob if second_best_prob > 0 else float('inf')
        else:
            discrimination_ratio = float('inf')

        # Calculate uncertainty (entropy-based)
        entropy = 0.0
        for cell_info in cell_data_list:
            p = cell_info['normalized_prob']
            if p > 0:
                entropy -= p * math.log2(p)

        # Maximum entropy for N cells
        max_entropy = math.log2(len(cell_data_list))
        uncertainty = entropy / max_entropy if max_entropy > 0 else 0.0

        # Determine quality status
        if confidence_score >= self.confidence_threshold and discrimination_ratio >= 2.0:
            status = "HIGH_CONFIDENCE"
        elif confidence_score >= 0.5:
            status = "MEDIUM_CONFIDENCE"
        elif confidence_score >= 0.3:
            status = "LOW_CONFIDENCE"
        else:
            status = "UNCERTAIN"

        # Return result
        result = {
            'miner_id': miner_id,
            'location': {
                'x': best_cell['x'],
                'y': best_cell['y'],
                'cell_id': best_cell['cell_id']
            },
            'confidence': round(confidence_score, 3),
            'metrics': {
                'discrimination_ratio': round(discrimination_ratio, 2),
                'uncertainty': round(uncertainty, 3),
                'valid_beacons': len(valid_beacons),
                'top_candidates': []
            },
            'status': status,
            'valid': confidence_score >= 0.3  # Minimum threshold
        }

        # Add top 3 candidates for debugging
        for i in range(min(3, len(cell_data_list))):
            cell = cell_data_list[i]
            result['metrics']['top_candidates'].append({
                'cell_id': cell['cell_id'],
                'x': cell['x'],
                'y': cell['y'],
                'confidence': round(cell['normalized_prob'], 3)
            })

        return result

    def _error_result(self, error_message):
        """Return standardized error result."""
        return {
            'miner_id': None,
            'location': None,
            'confidence': 0.0,
            'metrics': {
                'error': error_message,
                'valid_beacons': 0,
                'top_candidates': []
            },
            'status': 'LOCALIZATION_FAILED',
            'valid': False
        }

    def get_cell_coverage(self, cell_id):
        """Get beacon coverage statistics for a specific cell."""
        if cell_id not in self.radio_map['cells']:
            return None

        cell_data = self.radio_map['cells'][cell_id]
        beacon_stats = cell_data.get('beacon_stats', {})

        coverage = {
            'cell_id': cell_id,
            'x': cell_data['x'],
            'y': cell_data['y'],
            'beacons': {}
        }

        for beacon_id in self.beacon_ids:
            if beacon_id in beacon_stats:
                stats = beacon_stats[beacon_id]
                coverage['beacons'][beacon_id] = {
                    'mean': stats.get('mean'),
                    'std': stats.get('std'),
                    'samples': stats.get('samples', 0)
                }
            else:
                coverage['beacons'][beacon_id] = None

        return coverage

    def validate_rssi_range(self, rssi_vector):
        """Check if RSSI values are within reasonable range."""
        warnings = []

        for beacon_id, rssi_value in rssi_vector.items():
            if rssi_value == -100.0:
                continue

            if rssi_value > -40:
                warnings.append(f"Beacon {beacon_id}: RSSI {rssi_value} too high (possible proximity)")
            elif rssi_value < -95:
                warnings.append(f"Beacon {beacon_id}: RSSI {rssi_value} very weak (near detection limit)")

        return warning
