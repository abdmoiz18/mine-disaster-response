"""Terminal-based dashboard - no web server"""
import sqlite3
import os
import time

DB_PATH = os. path.expanduser('~/mine-disaster-response/gateway/rpi-scripts/mine_nav.db')

def show():
    os.system('clear')
    print("=" * 60)
    print("       MINE DISASTER RESPONSE - LIVE STATUS")
    print("=" * 60)
    
    if not os.path. exists(DB_PATH):
        print("Database not found!")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn. cursor()
        
        # Get latest miners
        cursor.execute('''
            SELECT device_id, estimated_x, estimated_y, confidence, path_length, timestamp
            FROM miner_telemetry
            WHERE id IN (SELECT MAX(id) FROM miner_telemetry GROUP BY device_id)
        ''')
        miners = cursor.fetchall()
        
        # Get total count
        cursor. execute('SELECT COUNT(*) FROM miner_telemetry')
        total = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n  Active Miners: {len(miners)}    Total Records: {total}")
        print("-" * 60)
        print(f"  {'MINER':<10} {'POSITION':<15} {'CONFIDENCE':<12} {'PATH':<10}")
        print("-" * 60)
        
        for m in miners:
            mid, x, y, conf, path_len, ts = m
            pos = f"({x:.1f}, {y:.1f})" if x else "(?, ?)"
            conf_str = f"{conf:.2f}" if conf else "N/A"
            path_str = f"{path_len} steps" if path_len else "N/A"
            print(f"  {mid:<10} {pos:<15} {conf_str:<12} {path_str:<10}")
        
        print("-" * 60)
        print(f"\n  Last update: {miners[0][5] if miners else 'N/A'}")
        print("\n  Press Ctrl+C to exit")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    print("Starting terminal dashboard...")
    try:
        while True:
            show()
            time. sleep(3)
    except KeyboardInterrupt:
        print("\nStopped.")