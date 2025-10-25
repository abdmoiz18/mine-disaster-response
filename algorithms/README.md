# Algorithms: Position Estimation and Pathfinding

**Last Updated:** 2025-10-25
**Owner:** Data Team

This directory contains the machine learning models and algorithms that form the "intelligence" of the Mine Disaster Response system.

## 1. Position Estimation via BLE Fingerprinting

The primary method for locating miners is BLE (Bluetooth Low Energy) Fingerprinting. This is a machine learning-based approach that is more robust than simple trilateration in complex indoor environments.

### How it Works

1.  **Data Collection (Training Phase):**
    *   A person walks through the mine, stopping at known `(x, y)` coordinates.
    *   At each coordinate, they record a "fingerprint": a snapshot of all visible BLE beacon IDs and their corresponding RSSI (signal strength) values.
    *   This creates a training dataset where the features are the RSSI values from the beacons, and the label is the `(x, y)` coordinate.

2.  **Model Training:**
    *   A model is trained on this dataset. A **k-Nearest Neighbors (k-NN)** classifier or a simple neural network are common choices.
    *   The model learns to associate a specific "fingerprint" of signal strengths with a specific location in the mine.

3.  **Inference (Real-time Operation):**
    *   A miner's device sends its current BLE fingerprint to the RPi gateway.
    *   The gateway feeds this fingerprint into the trained model.
    *   The model predicts the `(x, y)` coordinates for the miner.

### Action Plan

1.  **Create a Data Collection Script (`collect_data.py`):**
    *   This script will be run on a laptop or RPi to walk through the physical (or simulated) space.
    *   It will prompt for an `(x, y)` coordinate and then listen for a BLE scan to record the fingerprint, saving it to a `training_data.csv`.

2.  **Create a Model Training Script (`train_model.py`):**
    *   This script will read `training_data.csv`.
    *   It will use a library like `scikit-learn` to train a `KNeighborsClassifier`.
    *   The output will be a saved model file, e.g., `knn_position_model.pkl`.

3.  **Integrate the Model:**
    *   The `estimate_miner_position` function in `gateway/rpi-scripts/main_v2.py` will be updated to:
        a. Load `knn_position_model.pkl`.
        b. Take the incoming `ble_readings` and use the model to predict the position.

---

## 2. Pathfinding using A*

The secondary algorithm is A* (A-star) for pathfinding.

*   **Purpose:** To calculate the shortest, safest path from a miner's current location to a designated safe zone, avoiding obstacles.
*   **Status:** A stub for this function (`a_star_pathfinding`) exists in `main_v2.py`.
*   **Action Plan:** Implement the A* algorithm. It will need the mine grid layout (with walls/obstacles) as an input to navigate correctly.