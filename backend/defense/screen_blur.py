import time
from utils.logger import logger

class ScreenBlurController:
    """Screen blur with state machine. Only emits on state transitions."""
    
    # States
    STATE_OFF = 'off'
    STATE_PARTIAL = 'partial'
    STATE_FULL = 'full'
    
    def __init__(self, socketio=None):
        self.socketio = socketio
        self._current_state = self.STATE_OFF
        self._last_transition_time = 0
        self._min_transition_interval = 2.0  # Minimum seconds between state changes
        
    @property
    def is_active(self):
        return self._current_state != self.STATE_OFF
        
    def activate(self, intensity: str = 'partial', bounds: dict = None):
        """Activate blur overlay. Only emits if state actually changes."""
        now = time.time()
        new_state = self.STATE_FULL if intensity == 'full' else self.STATE_PARTIAL
        
        # Skip if already in this state and no bounds change
        if new_state == self._current_state and not bounds:
            return
            
        # Enforce minimum transition interval (prevent rapid toggling)
        if (now - self._last_transition_time) < self._min_transition_interval:
            return
            
        logger.info(f"Blur state: {self._current_state} → {new_state}")
        self._current_state = new_state
        self._last_transition_time = now
        
        if self.socketio:
            payload = {
                'action': 'blur_show',
                'intensity': intensity
            }
            if bounds:
                payload['bounds'] = bounds
            self.socketio.emit('defense_activated', payload)
                
    def deactivate(self):
        """Deactivate blur. Only emits if currently active."""
        if self._current_state == self.STATE_OFF:
            return  # Already off, don't re-emit
            
        logger.info(f"Blur state: {self._current_state} → off")
        self._current_state = self.STATE_OFF
        self._last_transition_time = time.time()
        
        if self.socketio:
            self.socketio.emit('defense_activated', {
                'action': 'blur_hide'
            })
    
    def reset(self):
        """Force reset state without emitting (for cleanup)."""
        self._current_state = self.STATE_OFF
        self._last_transition_time = 0
