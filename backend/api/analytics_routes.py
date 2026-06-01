from flask import Blueprint, jsonify
from database.db import db
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/summary', methods=['GET'])
def get_summary():
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Today's stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN observer_type = 'unknown' THEN 1 ELSE 0 END) as unknown_count,
                SUM(CASE WHEN threat_level IN ('HIGH', 'CRITICAL') THEN 1 ELSE 0 END) as high_risk,
                SUM(CASE WHEN observer_type = 'crossing' THEN 1 ELSE 0 END) as crossing_count
            FROM detection_event 
            WHERE date(timestamp) = date('now')
        """)
        today_row = cursor.fetchone()
        
        # Session stats
        cursor.execute("SELECT SUM(strftime('%s', end_time) - strftime('%s', start_time)) as active_time FROM session WHERE date(start_time) = date('now')")
        time_row = cursor.fetchone()
        active_seconds = time_row[0] if time_row and time_row[0] else 0
        active_hours = active_seconds / 3600.0
        
        return jsonify({
            'today': {
                'total_detections': today_row['total'] or 0,
                'unknown_observers': today_row['unknown_count'] or 0,
                'high_risk_incidents': today_row['high_risk'] or 0,
                'crossing_events': today_row['crossing_count'] or 0,
                'protected_hours': round(active_hours, 1)
            }
        })

@analytics_bp.route('/distribution', methods=['GET'])
def get_distribution():
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT observer_type, COUNT(*) as count FROM detection_event GROUP BY observer_type")
        types = {row['observer_type']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute("SELECT threat_level, COUNT(*) as count FROM detection_event GROUP BY threat_level")
        levels = {row['threat_level']: row['count'] for row in cursor.fetchall()}
        
        return jsonify({
            'by_observer_type': types,
            'by_threat_level': levels
        })
