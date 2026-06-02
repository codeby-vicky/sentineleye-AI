from typing import List
from risk_engine.decision_engine import DefenseAction
from defense.screen_blur import ScreenBlurController
from defense.window_manager import WindowManager
from defense.workstation_lock import lock_workstation
from defense.alert_manager import AlertManager
from utils.logger import logger

class DefenseService:
    def __init__(self, socketio=None):
        self.screen_blur = ScreenBlurController(socketio)
        self.window_manager = WindowManager()
        self.alert_manager = AlertManager(socketio)
        
    def execute_actions(self, actions: List[DefenseAction], threat_level: str = 'LOW'):
        """Execute a list of defense actions."""
        if not actions:
            # If no threat, make sure blur is off
            self.screen_blur.deactivate()
            return
            
        action_types = [a.action_type for a in actions]
        
        # Handle blur
        if 'blur' in action_types:
            blur_action = next(a for a in actions if a.action_type == 'blur')
            intensity = blur_action.parameters.get('intensity', 'partial')
            bounds = self.window_manager.get_active_window_bounds()
            self.screen_blur.activate(intensity, bounds)
        else:
            self.screen_blur.deactivate()
            
        # Handle minimize
        if 'minimize' in action_types:
            minimize_action = next(a for a in actions if a.action_type == 'minimize')
            target = minimize_action.parameters.get('target', 'sensitive')
            if target == 'all':
                self.window_manager.minimize_all_windows()
            else:
                self.window_manager.minimize_active_window()
                
        # Handle lock
        if 'lock' in action_types:
            lock_workstation()
            
        # Handle popup alerts
        if 'popup' in action_types:
            popup_action = next(a for a in actions if a.action_type == 'popup')
            message = popup_action.parameters.get('message', 'Unknown Threat')
            self.alert_manager.send_alert('popup', message, threat_level)
            
        # Handle autosave
        if 'autosave' in action_types:
            # Placeholder for autosave functionality (e.g., sending Ctrl+S)
            pass
