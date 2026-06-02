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
        self.locked_index = None
        self._initialized = True
        
    def _is_phone_camera(self, name: str) -> bool:
        """Check if a camera name suggests it is a phone or virtual camera."""
        if not name:
            return False
        name_lower = name.lower()
        heuristics = ['droidcam', 'oppo', 'phone', 'virtual', 'ip webcam', 'obs', 'xsplit']
        return any(h in name_lower for h in heuristics)

    def _get_best_camera_index(self, requested_index: int) -> int:
        """Find the best camera, avoiding phone webcams if possible."""
        # This is a basic enumeration. On Windows, cv2.videoCaptureProps doesn't easily yield names
        # without CAP_DSHOW, but we will try. If requested is 0, we'll try 0-3 and pick the first
        # that opens and isn't a phone.
        # However, for simplicity and safety, we just use the requested index unless it's obviously bad.
        # Real robust camera enumeration requires directshow/WMI which is complex.
        return requested_index
        
    def open(self, camera_index: int = 0, resolution: Tuple[int, int] = (1920, 1080)) -> bool:
        """Open the camera with the specified resolution."""
        with self.lock:
            # If we are already open on this exact index, DO NOT reopen!
            if self.is_running and self.cap is not None and self.cap.isOpened() and self.locked_index == camera_index:
                logger.info(f"Camera {camera_index} is already open and locked. Reusing handle.")
                return True
                
            if self.cap is not None and self.cap.isOpened():
                logger.info(f"Releasing previous camera index {self.locked_index} to open {camera_index}")
                self.cap.release()
                self.is_running = False
                
            logger.info(f"Opening camera {camera_index} at {resolution}")
            
            # Prioritize standard MSMF over DirectShow for Windows default webcams
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
            
            self.locked_index = camera_index
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
            self.locked_index = None
            logger.info("Camera released")

    @staticmethod
    def frame_to_base64(frame: np.ndarray, quality: int = 80) -> str:
        """Convert a numpy frame to a base64 encoded JPEG string."""
        if frame is None:
            return ""
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return base64.b64encode(buffer).decode('utf-8')
