import mss
import mss.tools
import numpy as np
import cv2
from typing import Optional, Tuple
from utils.logger import logger

class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()
        self.last_hash = None
        logger.info("Screen Capture service initialized")
        
    def _dhash(self, image: np.ndarray, hash_size: int = 8) -> str:
        """Calculate difference hash (dHash) for an image to detect changes."""
        # Convert to grayscale and resize to (hash_size + 1, hash_size)
        resized = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (hash_size + 1, hash_size))
        # Compute differences between adjacent pixels
        diff = resized[:, 1:] > resized[:, :-1]
        # Convert binary array to hex string
        return sum([2 ** i for (i, v) in enumerate(diff.flatten()) if v])

    def capture_screen(self, monitor_index: int = 1) -> Optional[np.ndarray]:
        """
        Capture the entire screen.
        monitor_index: 0 is all monitors, 1 is primary monitor.
        """
        try:
            if monitor_index >= len(self.sct.monitors):
                logger.warning(f"Monitor {monitor_index} not found. Falling back to primary.")
                monitor_index = 1
                
            monitor = self.sct.monitors[monitor_index]
            sct_img = self.sct.grab(monitor)
            
            # Convert to numpy array (BGRA to BGR)
            img = np.array(sct_img)
            return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return None

    def has_screen_changed(self, frame: np.ndarray, threshold: int = 10) -> bool:
        """
        Check if screen has changed significantly using dHash.
        Returns True if changed, False otherwise.
        """
        if frame is None:
            return False
            
        current_hash = self._dhash(frame)
        
        if self.last_hash is None:
            self.last_hash = current_hash
            return True
            
        # Count bits difference (Hamming distance)
        diff = bin(self.last_hash ^ current_hash).count('1')
        
        if diff > threshold:
            self.last_hash = current_hash
            return True
            
        return False
        
    def get_active_window_title(self) -> str:
        """Fetch the title of the currently active window on Windows."""
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    return buf.value
            return ""
        except Exception as e:
            logger.error(f"Failed to get active window title: {e}")
            return ""
