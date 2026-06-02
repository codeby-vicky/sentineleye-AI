from utils.logger import logger

class ScreenBlurController:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.is_active = False
        
    def activate(self, intensity: str = 'partial', bounds: dict = None):
        """Activate the screen blur overlay via Electron."""
        if not self.is_active or bounds: # Allow updating bounds even if active
            logger.info(f"Activating screen blur ({intensity})")
            self.is_active = True
            if self.socketio:
                payload = {
                    'action': 'blur_show',
                    'intensity': intensity
                }
                if bounds:
                    payload['bounds'] = bounds
                self.socketio.emit('defense_activated', payload)
                
    def deactivate(self):
        """Deactivate the screen blur overlay."""
        if self.is_active:
            logger.info("Deactivating screen blur")
            self.is_active = False
            if self.socketio:
                self.socketio.emit('defense_activated', {
                    'action': 'blur_hide'
                })
