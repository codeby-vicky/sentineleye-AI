import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict
from config import Config
from utils.logger import logger
from utils.helpers import numpy_to_bytes, bytes_to_numpy, generate_timestamp
import numpy as np

class DatabaseManager:
    def __init__(self, db_path: str = Config.DATABASE_PATH):
        self.db_path = db_path
        Config.init_app()

    @contextmanager
    def get_connection(self):
        """Yields a SQLite connection with row factory configured."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        """Initialize database tables and default settings."""
        logger.info(f"Initializing database at {self.db_path}")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL;")
            
            # Create Tables
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS owner (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    face_embedding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS trusted_user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    relationship TEXT CHECK(relationship IN ('friend', 'colleague', 'family', 'owner')) NOT NULL,
                    face_embedding BLOB NOT NULL,
                    trust_level REAL DEFAULT 0.8 CHECK(trust_level >= 0.0 AND trust_level <= 1.0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS session (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    total_detections INTEGER DEFAULT 0,
                    unknown_count INTEGER DEFAULT 0,
                    trusted_count INTEGER DEFAULT 0,
                    crossing_count INTEGER DEFAULT 0,
                    high_risk_count INTEGER DEFAULT 0,
                    avg_threat_score REAL DEFAULT 0.0
                );

                CREATE TABLE IF NOT EXISTS detection_event (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER REFERENCES session(id),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observer_type TEXT CHECK(observer_type IN ('owner', 'trusted', 'unknown', 'crossing')) NOT NULL,
                    observer_id INTEGER REFERENCES trusted_user(id),
                    observer_name TEXT,
                    gaze_score REAL DEFAULT 0.0,
                    persistence_seconds REAL DEFAULT 0.0,
                    screen_sensitivity TEXT CHECK(screen_sensitivity IN ('safe', 'personal', 'confidential', 'highly_confidential')),
                    threat_score REAL DEFAULT 0.0,
                    threat_level TEXT CHECK(threat_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
                    action_taken TEXT,
                    reason TEXT
                );

                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT CHECK(category IN ('general', 'monitoring', 'defense', 'notification')),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS alert_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    detection_event_id INTEGER REFERENCES detection_event(id),
                    alert_type TEXT CHECK(alert_type IN ('popup', 'blur', 'minimize', 'lock')),
                    message TEXT,
                    acknowledged BOOLEAN DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_detection_timestamp ON detection_event(timestamp);
                CREATE INDEX IF NOT EXISTS idx_detection_session ON detection_event(session_id);
                CREATE INDEX IF NOT EXISTS idx_detection_type ON detection_event(observer_type);
                CREATE INDEX IF NOT EXISTS idx_alert_event ON alert_log(detection_event_id);
            """)
            conn.commit()
            
            self._insert_default_settings(cursor)
            conn.commit()
            logger.info("Database initialization complete.")

    def _insert_default_settings(self, cursor):
        """Insert default settings if they don't exist."""
        defaults = [
            ('camera_index', '0', 'general'),
            ('gaze_threshold', '15', 'monitoring'),
            ('persistence_threshold', '5', 'monitoring'),
            ('ocr_interval', '5', 'monitoring'),
            ('crossing_detection', 'true', 'monitoring'),
            ('defense_low_popup', 'true', 'defense'),
            ('defense_medium_blur', 'true', 'defense'),
            ('defense_medium_autosave', 'true', 'defense'),
            ('defense_high_minimize', 'true', 'defense'),
            ('defense_high_blur', 'true', 'defense'),
            ('defense_high_autosave', 'true', 'defense'),
            ('defense_critical_lock', 'true', 'defense'),
            ('defense_critical_blur', 'true', 'defense'),
            ('sound_enabled', 'true', 'notification'),
            ('popup_duration', '5', 'notification')
        ]
        
        for key, value, category in defaults:
            cursor.execute("""
                INSERT OR IGNORE INTO settings (key, value, category) 
                VALUES (?, ?, ?)
            """, (key, value, category))

    # --- OWNER ---
    def set_owner(self, name: str, embedding: np.ndarray) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Deactivate existing owner
            cursor.execute("UPDATE owner SET is_active = 0")
            
            cursor.execute("""
                INSERT INTO owner (name, face_embedding, is_active)
                VALUES (?, ?, 1)
            """, (name, numpy_to_bytes(embedding)))
            conn.commit()
            return True

    def get_owner(self) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM owner WHERE is_active = 1 LIMIT 1")
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d['face_embedding'] = bytes_to_numpy(d['face_embedding'])
                return d
            return None

    # --- TRUSTED USERS ---
    def add_trusted_user(self, name: str, relationship: str, embedding: np.ndarray, trust_level: float = 0.8) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trusted_user (name, relationship, face_embedding, trust_level)
                VALUES (?, ?, ?, ?)
            """, (name, relationship, numpy_to_bytes(embedding), trust_level))
            conn.commit()
            return cursor.lastrowid

    def get_trusted_users(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trusted_user WHERE is_active = 1")
            users = []
            for row in cursor.fetchall():
                d = dict(row)
                d['face_embedding'] = bytes_to_numpy(d['face_embedding'])
                users.append(d)
            return users

    def delete_trusted_user(self, user_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE trusted_user SET is_active = 0 WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- SESSIONS ---
    def create_session(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO session DEFAULT VALUES")
            conn.commit()
            return cursor.lastrowid

    def end_session(self, session_id: int, stats: dict):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE session SET 
                    end_time = CURRENT_TIMESTAMP,
                    total_detections = ?,
                    unknown_count = ?,
                    trusted_count = ?,
                    crossing_count = ?,
                    high_risk_count = ?,
                    avg_threat_score = ?
                WHERE id = ?
            """, (
                stats.get('total_detections', 0),
                stats.get('unknown_count', 0),
                stats.get('trusted_count', 0),
                stats.get('crossing_count', 0),
                stats.get('high_risk_count', 0),
                stats.get('avg_threat_score', 0.0),
                session_id
            ))
            conn.commit()

    # --- EVENTS ---
    def log_event(self, session_id: int, event_data: dict) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO detection_event (
                    session_id, observer_type, observer_id, observer_name,
                    gaze_score, persistence_seconds, screen_sensitivity,
                    threat_score, threat_level, action_taken, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                event_data.get('observer_type'),
                event_data.get('observer_id'),
                event_data.get('observer_name'),
                event_data.get('gaze_score', 0.0),
                event_data.get('persistence_seconds', 0.0),
                event_data.get('screen_sensitivity', 'safe'),
                event_data.get('threat_score', 0.0),
                event_data.get('threat_level', 'LOW'),
                event_data.get('action_taken', ''),
                event_data.get('reason', '')
            ))
            conn.commit()
            return cursor.lastrowid

    def get_events(self, limit: int = 50, offset: int = 0, filters: dict = None) -> tuple[List[Dict], int]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM detection_event"
            count_query = "SELECT COUNT(*) FROM detection_event"
            params = []
            
            if filters:
                conditions = []
                if filters.get('observer_type') and filters['observer_type'] != 'all':
                    conditions.append("observer_type = ?")
                    params.append(filters['observer_type'])
                if filters.get('threat_level') and filters['threat_level'] != 'all':
                    conditions.append("threat_level = ?")
                    params.append(filters['threat_level'])
                
                if conditions:
                    where_clause = " WHERE " + " AND ".join(conditions)
                    query += where_clause
                    count_query += where_clause
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(count_query, params[:-2] if params else [])
            total_count = cursor.fetchone()[0]
            
            cursor.execute(query, params)
            events = [dict(row) for row in cursor.fetchall()]
            
            return events, total_count

    # --- SETTINGS ---
    def get_all_settings(self) -> Dict[str, str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {row['key']: row['value'] for row in cursor.fetchall()}

    def update_setting(self, key: str, value: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?
            """, (value, key))
            conn.commit()

# Singleton instance
db = DatabaseManager()
