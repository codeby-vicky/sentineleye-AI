from database.db import db
from utils.logger import logger

class AlertManager:
    def __init__(self, socketio=None):
        self.socketio = socketio
        
    def send_alert(self, alert_type: str, message: str, threat_level: str):
        """Send an alert to the frontend via WebSocket."""
        logger.info(f"Dispatching alert [{threat_level}]: {message}")
        if self.socketio:
            settings = db.get_all_settings()
            sound_enabled = settings.get('sound_enabled', 'true') == 'true'
            
            self.socketio.emit('threat_detected', {
                'level': threat_level,
                'reason': message,
                'play_sound': sound_enabled
            })
            
    def log_alert(self, detection_event_id: int, alert_type: str, message: str):
        """Log an alert action to the database."""
        # Simple wrapper around db.py, could be expanded.
        pass
