import time
from database.db import db
from utils.logger import logger

class AlertManager:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self._last_alert_time = 0
        self._last_alert_level = None
        self._cooldown_seconds = 10  # Minimum seconds between alerts
        
    def send_alert(self, alert_type: str, message: str, threat_level: str):
        """Send an alert to the frontend via WebSocket. Respects cooldowns and state changes."""
        now = time.time()
        
        # Only send if: level changed OR cooldown expired
        level_changed = threat_level != self._last_alert_level
        cooldown_ok = (now - self._last_alert_time) >= self._cooldown_seconds
        
        if not level_changed and not cooldown_ok:
            return  # Suppress duplicate alert
        
        logger.info(f"Dispatching alert [{threat_level}]: {message}")
        self._last_alert_time = now
        self._last_alert_level = threat_level
        
        if self.socketio:
            settings = db.get_all_settings()
            sound_enabled = settings.get('sound_enabled', 'true') == 'true'
            
            self.socketio.emit('threat_detected', {
                'level': threat_level,
                'reason': message,
                'play_sound': sound_enabled and level_changed  # Only play sound on level change
            })
            
    def clear_state(self):
        """Reset alert state (called when monitoring stops)."""
        self._last_alert_level = None
        self._last_alert_time = 0
            
    def log_alert(self, detection_event_id: int, alert_type: str, message: str):
        """Log an alert action to the database."""
        pass
