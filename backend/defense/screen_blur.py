from utils.logger import logger
import threading
import time
import base64
import cv2
import mss
import numpy as np

class ScreenBlurController:
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.is_active = False
        self.current_bounds = None
        self.current_intensity = 'partial'
        self.blur_thread = None
        
    def _blur_loop(self):
        with mss.mss() as sct:
            while self.is_active:
                try:
                    if self.current_bounds and self.current_bounds.get('w', 0) > 0 and self.current_bounds.get('h', 0) > 0:
                        # Capture specific region
                        monitor = {
                            "top": self.current_bounds['y'],
                            "left": self.current_bounds['x'],
                            "width": self.current_bounds['w'],
                            "height": self.current_bounds['h']
                        }
                    else:
                        # Full screen fallback (primary monitor is sct.monitors[1])
                        monitor = sct.monitors[1]
                        
                        img = np.array(sct.grab(monitor))
                        
                        # Apply OpenCV blur (fast CPU blur)
                        kernel_size = 41 if self.current_intensity == 'full' else 21
                        blurred = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)
                        
                        # Add frosted glass white tint
                        overlay = np.full_like(blurred, 255)
                        alpha = 0.15 if self.current_intensity == 'full' else 0.1
                        blurred = cv2.addWeighted(overlay, alpha, blurred, 1 - alpha, 0)
                        
                        # Encode to JPG (quality 60 is plenty for a blurred image)
                        _, buffer = cv2.imencode('.jpg', blurred, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                        frame_b64 = base64.b64encode(buffer).decode('utf-8')
                        
                        if self.socketio:
                            self.socketio.emit('blur_frame', {'frame': frame_b64})
                            
                except Exception as e:
                    logger.error(f"Error in blur loop: {e}")
                    
                time.sleep(0.1)  # ~10 FPS

        
    def activate(self, intensity: str = 'partial', bounds: dict = None):
        """Activate the screen blur overlay."""
        self.current_bounds = bounds
        self.current_intensity = intensity
        
        if not self.is_active:
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
                
            # Start blur generation thread
            if self.blur_thread is None or not self.blur_thread.is_alive():
                self.blur_thread = threading.Thread(target=self._blur_loop, daemon=True)
                self.blur_thread.start()
                
    def deactivate(self):
        """Deactivate the screen blur overlay."""
        if self.is_active:
            logger.info("Deactivating screen blur")
            self.is_active = False
            if self.socketio:
                self.socketio.emit('defense_activated', {
                    'action': 'blur_hide'
                })
