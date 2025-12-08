# File: generate_radio_map.py
# Run this AFTER collecting data from cells

import json
import glob
import os
from datetime import datetime

def aggregate_collected_data(data_dir="."):
    """Find all collected cell data and aggregate into radio map format"""
    
    # Look for all statistics JSON files
    stat_files = glob.glob(os.path.join(data_dir, "*_stats.json"))
    
    cells = {}
    
    for stat_file in stat_files:
        try:
            with open(stat_file, 'r') as f:
                data = json.load(f)
            
            cell_id = data['cell_id']
            
            # Convert to format expected by FingerprintMatcher
            cells[cell_id] = {
                'x': int(data['x']),  # Grid x coordinate
                'y': int(data['y']),  # Grid y coordinate
                'beacon_stats': {}
            }
            
            # Add beacon statistics
            for beacon_id, stats in data['beacon_stats'].items():
                if stats:  # If we have data for this beacon
                    cells[cell_id]['beacon_stats'][beacon_id] = {
                        'mean': stats['mean'],
                        'std': stats['std'],
                        'samples': stats['samples'],
                        'min': stats['min'],
                        'max': stats['max']
                    }
                else:
                    # No data for this beacon at this cell
                    cells[cell_id]['beacon_stats'][beacon_id] = {
                        'mean': -100.0,  # Indicates no signal
                        'std': 0.0,
                        'samples': 0,
                        'min': -100,
                        'max': -100
                    }
            
            print(f"✓ Added cell {cell_id}")
            
        except Exception as e:
            print(f"✗ Error processing {stat_file}: {e}")
    
    return cells

def create_radio_map_json(cells, output_file="radio_map.json"):
    """Create the final radio_map.json file"""
    
    # Get beacon positions (you need to fill these in!)
    beacon_positions = {
        "B1": {"position": [0.0, 0.0], "tx_power": -12},
        "B2": {"position": [11.0, 0.0], "tx_power": -12},
        "B3": {"position": [5.0, 7.0], "tx_power": -12}
    }
    
    radio_map = {
        "metadata": {
            "creation_date": datetime.now().isoformat(),
            "grid_resolution": 1.0,
            "total_cells": len(cells),
            "cells_collected": list(cells.keys()),
            "beacon_config": beacon_positions,
            "notes": "MVP radio map for demonstration"
        },
        "cells": cells
    }
    
    with open(output_file, 'w') as f:
        json.dump(radio_map, f, indent=2)
    
    print(f"\n✅ Created {output_file} with {len(cells)} cells")
    return radio_map

def quick_test_radio_map(radio_map_file):
    """Quick test to verify the radio map works with FingerprintMatcher"""
    try:
        from FingerprintMatcher import FingerprintMatcher  # Adjust import as needed
        
        matcher = FingerprintMatcher(radio_map_file)
        
        # Test with sample RSSI
        test_rssi = {"B1": -65.5, "B2": -72.0, "B3": -68.8}
        result = matcher.locate_miner(test_rssi, "test_miner")
        
        print("\n" + "="*50)
        print("TEST RESULT:")
        print(f"Location: {result.get('location')}")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Status: {result.get('status')}")
        print(f"Valid: {result.get('valid')}")
        print("="*50)
        
        return result
        
    except ImportError:
        print("⚠️  Could not import FingerprintMatcher - check your imports")
        return None
    except Exception as e:
        print(f"⚠️  Test failed: {e}")
        return None

if __name__ == "__main__":
    print("="*60)
    print("RADIO MAP GENERATOR - MVP VERSION")
    print("="*60)
    
    # Step 1: Aggregate collected data
    print("\n1. Searching for collected cell data...")
    cells = aggregate_collected_data()
    
    if not cells:
        print("❌ No cell data found! Please collect data first.")
        print("\nTo collect data, run the ESP32 collection script at each cell.")
        print("Expected files: A1_stats.json, A2_stats.json, etc.")
        exit(1)
    
    # Step 2: Create the radio map
    print(f"\n2. Creating radio map with {len(cells)} cells...")
    radio_map = create_radio_map_json(cells, "radio_map.json")
    
    # Step 3: Quick test
    print("\n3. Testing radio map...")
    test_result = quick_test_radio_map("radio_map.json")
    
    if test_result and test_result.get('valid'):
        print("\n🎉 SUCCESS! Radio map is working!")
        print("\nNext steps:")
        print("1. Copy radio_map.json to your Raspberry Pi system")
        print("2. Update FingerprintMatcher to use this new file")
        print("3. Test with actual miner device")
    else:
        print("\n⚠️  Radio map created but test failed.")
        print("Check that your collected data has reasonable RSSI values.")
    
    print("\n" + "="*60)

