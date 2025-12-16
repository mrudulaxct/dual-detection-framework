"""
Database Management
Stores system data, detection results, and logs
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

class Database:
    def __init__(self, db_path='data/system.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # System data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                state TEXT,
                output REAL,
                control TEXT,
                reference REAL
            )
        ''')
        
        # Detection results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                fault_statistic REAL,
                fault_detected INTEGER,
                attack_statistic REAL,
                attack_detected INTEGER,
                anomaly_type TEXT
            )
        ''')
        
        # Anomaly events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS anomaly_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                event_type TEXT,
                magnitude REAL,
                description TEXT
            )
        ''')
        
        # Network statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                packets_sent INTEGER,
                packets_encrypted INTEGER,
                packets_attacked INTEGER
            )
        ''')
        
        self.conn.commit()
    
    def save_system_data(self, timestamp, state, output, control, reference):
        """Save system data"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO system_data (timestamp, state, output, control, reference)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, json.dumps(state.tolist()), output, json.dumps(control.tolist()), reference))
        self.conn.commit()
    
    def save_detection_results(self, timestamp, fault_stat, fault_det, attack_stat, attack_det, anomaly_type):
        """Save detection results"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO detections (timestamp, fault_statistic, fault_detected, 
                                   attack_statistic, attack_detected, anomaly_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, fault_stat, int(fault_det), attack_stat, int(attack_det), anomaly_type))
        self.conn.commit()
    
    def save_anomaly_event(self, timestamp, event_type, magnitude, description):
        """Save anomaly event"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO anomaly_events (timestamp, event_type, magnitude, description)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, event_type, magnitude, description))
        self.conn.commit()
    
    def save_network_stats(self, timestamp, stats):
        """Save network statistics"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO network_stats (timestamp, packets_sent, packets_encrypted, packets_attacked)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, stats['packets_sent'], stats['packets_encrypted'], stats['packets_attacked']))
        self.conn.commit()
    
    def get_recent_data(self, limit=100):
        """Get recent system data"""
        cursor = self.conn.cursor()
        
        # Get system data
        cursor.execute('''
            SELECT timestamp, state, output, control, reference
            FROM system_data
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        system_data = cursor.fetchall()
        
        # Get detection results
        cursor.execute('''
            SELECT timestamp, fault_statistic, fault_detected, attack_statistic, attack_detected, anomaly_type
            FROM detections
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        detection_data = cursor.fetchall()
        
        return {
            'system': system_data,
            'detections': detection_data
        }
    
    def get_anomaly_events(self, limit=50):
        """Get recent anomaly events"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT timestamp, event_type, magnitude, description
            FROM anomaly_events
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def clear_old_data(self, keep_last_n=10000):
        """Clear old data to prevent database bloat"""
        cursor = self.conn.cursor()
        
        # Keep only last N records in each table
        for table in ['system_data', 'detections', 'network_stats']:
            cursor.execute(f'''
                DELETE FROM {table}
                WHERE id NOT IN (
                    SELECT id FROM {table}
                    ORDER BY id DESC
                    LIMIT ?
                )
            ''', (keep_last_n,))
        
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        self.conn.close()