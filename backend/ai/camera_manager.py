import cv2
import threading
import base64
import numpy as np
from typing import Tuple, Optional
from utils.logger import logger

class CameraManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CameraManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self.cap = None
        self.lock = threading.Lock()
        self.resolution = (1920, 1080)
        self.is_running = False
        self._initialized = True
        
    def open(self, camera_index: int = 0, resolution: Tuple[int, int] = (1920, 1080)) -> bool:
        """Open the camera with the specified resolution."""
        with self.lock:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()
                
            logger.info(f"Opening camera {camera_index} at {resolution}")
            
            backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, cv2.CAP_ANY]
            for backend in backends:
                self.cap = cv2.VideoCapture(camera_index, backend)
                if self.cap.isOpened():
                    logger.info(f"Successfully opened camera {camera_index} using backend {backend}")
                    break
                    
            if self.cap is None or not self.cap.isOpened():
                logger.error(f"Failed to open camera {camera_index} with any backend")
                return False
                
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Read actual resolution set
            actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.resolution = (actual_w, actual_h)
            logger.info(f"Camera opened successfully. Actual resolution: {actual_w}x{actual_h}")
            
            self.is_running = True
            return True
            
    def read_frame(self) -> Optional[np.ndarray]:
        """Read a frame from the camera in a thread-safe manner."""
        if not self.is_running or self.cap is None:
            return None
            
        with self.lock:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Failed to read frame from camera")
                return None
            return frame
            
    def release(self):
        """Release the camera resources."""
        with self.lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self.is_running = False
            logger.info("Camera released")

    @staticmethod
    def frame_to_base64(frame: np.ndarray, quality: int = 80) -> str:
        """Convert a numpy frame to a base64 encoded JPEG string."""
        if frame is None:
            return ""
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return base64.b64encode(buffer).decode('utf-8')
