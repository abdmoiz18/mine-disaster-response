import numpy as np
from collections import deque
import math

class RSSIPreprocessor:
    def __init__(self, alpha=0.3, outlier_threshold_db=15, min_samples=5, max_history=10):
        """
        Production-ready RSSI preprocessor with confidence scoring.

        Parameters:
        - alpha: Exponential smoothing factor (0-1, higher = more responsive)
        - outlier_threshold_db: Threshold for outlier removal (± dB from median)
        - min_samples: Minimum samples required for reliable processing
        - max_history: Maximum history length for trend analysis
        """
        self.alpha = alpha
        self.outlier_threshold = outlier_threshold_db
        self.min_samples = min_samples
        self.max_history = max_history

        # State tracking per miner-beacon pair
        self.state_history = {}

    def _initialize_miner_state(self, miner_id):
        """Initialize state tracking for new miner."""
        if miner_id not in self.state_history:
            self.state_history[miner_id] = {
                'B1': {'values': deque(maxlen=self.max_history), 'stability': 1.0},
                'B2': {'values': deque(maxlen=self.max_history), 'stability': 1.0},
                'B3': {'values': deque(maxlen=self.max_history), 'stability': 1.0}
            }

    def _calculate_beacon_confidence(self, samples, beacon_id, miner_id):
        """
        Calculate confidence score for a beacon's RSSI reading.
        Returns: confidence (0.0-1.0), diagnostics dict
        """
        if not samples or len(samples) == 0:
            return 0.0, {'reason': 'no_samples', 'count': 0}

        # Count-based confidence
        sample_count = len(samples)
        count_confidence = min(1.0, sample_count / 20.0)  # 20 samples = max confidence

        # Variance-based confidence
        variance = np.var(samples) if len(samples) > 1 else 0
        # Lower variance = higher confidence
        var_confidence = max(0.0, 1.0 - (variance / 100.0))  # Normalize

        # Range-based confidence (detect clipping or extreme values)
        rssi_range = max(samples) - min(samples) if len(samples) > 1 else 0
        range_confidence = max(0.0, 1.0 - (rssi_range / 40.0))  # >40 dB range suspicious

        # Stability confidence (trend over time)
        stability = self._calculate_stability_confidence(miner_id, beacon_id, np.median(samples))

        # Combined confidence with weights
        weights = {
            'count': 0.3,
            'variance': 0.3,
            'range': 0.2,
            'stability': 0.2
        }

        total_confidence = (
            count_confidence * weights['count'] +
            var_confidence * weights['variance'] +
            range_confidence * weights['range'] +
            stability * weights['stability']
        )

        # Penalize if insufficient samples
        if sample_count < self.min_samples:
            total_confidence *= 0.5

        # Diagnostics for debugging
        diagnostics = {
            'sample_count': sample_count,
            'variance': round(variance, 2),
            'range': rssi_range,
            'stability': round(stability, 2),
            'component_scores': {
                'count': round(count_confidence, 2),
                'variance': round(var_confidence, 2),
                'range': round(range_confidence, 2),
                'stability': round(stability, 2)
            }
        }

        return min(1.0, max(0.0, total_confidence)), diagnostics

    def _calculate_stability_confidence(self, miner_id, beacon_id, current_median):
        """Calculate stability based on historical consistency."""
        if miner_id not in self.state_history:
            return 1.0  # No history, assume stable

        history = self.state_history[miner_id][beacon_id]['values']
        if len(history) < 2:
            return 1.0

        # Calculate how much current value deviates from historical trend
        recent_avg = np.mean(list(history)[-3:]) if len(history) >= 3 else np.mean(history)
        deviation = abs(current_median - recent_avg)

        # Small deviation = high stability
        if deviation < 5:
            return 1.0
        elif deviation < 10:
            return 0.7
        elif deviation < 15:
            return 0.4
        else:
            return 0.2

    def _remove_outliers(self, samples):
        """Remove outliers using modified Z-score method."""
        if not samples or len(samples) < 3:
            return samples.copy() if samples else []

        samples_array = np.array(samples)
        median = np.median(samples_array)
        mad = np.median(np.abs(samples_array - median))

        if mad == 0:
            return samples.copy()

        modified_z_scores = 0.6745 * (samples_array - median) / mad
        filtered = samples_array[np.abs(modified_z_scores) < 3.5]

        # If we filtered out too much, return original
        if len(filtered) < len(samples) * 0.5:
            return samples.copy()

        return filtered.tolist()

    def _exponential_smoothing(self, current_value, previous_value):
        """Apply exponential smoothing."""
        if previous_value is None:
            return current_value
        return self.alpha * current_value + (1 - self.alpha) * previous_value

    def process_miner_rssi(self, miner_id, raw_samples, previous_smoothed=None):
        """
        Main processing function for a single miner.

        Parameters:
        - miner_id: String identifier (M01-M05)
        - raw_samples: Dict {beacon_id: [rssi_values]}
        - previous_smoothed: Dict {beacon_id: previous_smoothed_value} or None

        Returns:
        Dict with processed RSSI values, confidence scores, and diagnostics.
        """
        # Initialize state tracking
        self._initialize_miner_state(miner_id)

        # Default previous values if not provided
        if previous_smoothed is None:
            previous_smoothed = {'B1': None, 'B2': None, 'B3': None}

        # Initialize results structure
        results = {
            'miner_id': miner_id,
            'processed_rssi': {},
            'beacon_confidence': {},
            'overall_confidence': 0.0,
            'beacon_diagnostics': {},
            'quality_flags': {
                'sufficient_samples': False,
                'stable_readings': False,
                'beacon_coverage': 0
            },
            'timestamp': None  # To be set by caller
        }

        beacon_confidences = []
        valid_beacon_count = 0

        # Process each beacon
        for beacon_id in ['B1', 'B2', 'B3']:
            samples = raw_samples.get(beacon_id, [])

            # Handle missing beacon
            if not samples or len(samples) == 0:
                results['processed_rssi'][beacon_id] = -100.0
                results['beacon_confidence'][beacon_id] = 0.0
                results['beacon_diagnostics'][beacon_id] = {
                    'status': 'missing',
                    'reason': 'no_samples_detected'
                }
                continue

            # Step 1: Remove outliers
            cleaned_samples = self._remove_outliers(samples)

            # Step 2: Calculate robust median (middle 50% range)
            if cleaned_samples:
                sorted_samples = sorted(cleaned_samples)
                n = len(sorted_samples)
                lower_idx = n // 4
                upper_idx = (3 * n) // 4
                central_samples = sorted_samples[lower_idx:upper_idx]
                current_median = np.median(central_samples) if central_samples else np.median(sorted_samples)
            else:
                current_median = np.median(samples)

            # Step 3: Apply exponential smoothing
            previous_value = previous_smoothed.get(beacon_id)
            smoothed_value = self._exponential_smoothing(current_median, previous_value)

            # Step 4: Calculate confidence
            confidence, diagnostics = self._calculate_beacon_confidence(
                cleaned_samples, beacon_id, miner_id
            )

            # Update state history
            self.state_history[miner_id][beacon_id]['values'].append(smoothed_value)

            # Store results
            results['processed_rssi'][beacon_id] = round(float(smoothed_value), 1)
            results['beacon_confidence'][beacon_id] = round(float(confidence), 3)
            results['beacon_diagnostics'][beacon_id] = diagnostics

            # Track for overall confidence
            if confidence > 0.3:  # Minimum threshold
                beacon_confidences.append(confidence)
                valid_beacon_count += 1

        # Calculate overall metrics
        if beacon_confidences:
            results['overall_confidence'] = round(float(np.mean(beacon_confidences)), 3)
        else:
            results['overall_confidence'] = 0.0

        # Set quality flags
        results['quality_flags']['sufficient_samples'] = (
            all(len(raw_samples.get(b, [])) >= self.min_samples for b in ['B1', 'B2', 'B3'])
        )
        results['quality_flags']['stable_readings'] = (
            results['overall_confidence'] >= 0.7
        )
        results['quality_flags']['beacon_coverage'] = valid_beacon_count

        # Determine overall status
        if valid_beacon_count >= 2 and results['overall_confidence'] >= 0.7:
            results['status'] = 'HIGH_CONFIDENCE'
        elif valid_beacon_count >= 2 and results['overall_confidence'] >= 0.5:
            results['status'] = 'MEDIUM_CONFIDENCE'
        elif valid_beacon_count >= 1:
            results['status'] = 'LOW_CONFIDENCE'
        else:
            results['status'] = 'NO_VALID_DATA'

        return results

    def reset_miner_history(self, miner_id):
        """Reset history for a specific miner."""
        if miner_id in self.state_history:
            for beacon_id in ['B1', 'B2', 'B3']:
                self.state_history[miner_id][beacon_id]['values'].clear()
                self.state_history[miner_id][beacon_id]['stability'] = 1.0

    def get_miner_statistics(self, miner_id):

        if miner_id not in self.state_history:
            return None

        stats = {}
        for beacon_id in ['B1', 'B2', 'B3']:
            values = list(self.state_history[miner_id][beacon_id]['values'])
            if values:
                stats[beacon_id] = {
                    'history_length': len(values),
                    'mean': round(float(np.mean(values)), 1),
                    'std': round(float(np.std(values)), 2) if len(values) > 1 else 0.0,
                    'trend': self._calculate_trend(values),
                    'latest': values[-1] if values else None
                }
            else:
                stats[beacon_id] = {'history_length': 0, 'mean': None, 'std': None, 'trend': None}

        return stats

    def _calculate_trend(self, values):
        """Calculate simple trend (increasing, decreasing, stable)."""
        if len(values) < 3:
            return 'insufficient_data'

        recent = values[-3:]
        if recent[2] > recent[0] + 1:
            return 'increasing'
        elif recent[2] < recent[0] - 1:
            return 'decreasing'
        else:
            return 'stable'
