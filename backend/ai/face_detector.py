import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass
from typing import List, Tuple, Dict
from utils.logger import logger

@dataclass
class DetectedFace:
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    keypoints: Dict[str, Tuple[int, int]]

class FaceDetector:
    def __init__(self):
        logger.info("Initializing MediaPipe Face Detector...")
        self.mp_face_detection = mp.solutions.face_detection
        # model_selection=1 is for full-range (further away), 0 is short-range (<2m)
        self.detector = self.mp_face_detection.FaceDetection(
            model_selection=1, 
            min_detection_confidence=0.5
        )
        
    def detect(self, frame: np.ndarray) -> List[DetectedFace]:
        """
        Detect faces in a BGR image frame.
        Returns a list of DetectedFace objects.
        """
        if frame is None:
            return []
            
        results = []
        h, w, _ = frame.shape
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        try:
            # Run inference
            detection_results = self.detector.process(rgb_frame)
            
            if not detection_results.detections:
                return []
                
            for detection in detection_results.detections:
                # Get bounding box relative to image size
                bboxC = detection.location_data.relative_bounding_box
                
                # Convert to pixel coordinates
                x = int(bboxC.xmin * w)
                y = int(bboxC.ymin * h)
                width = int(bboxC.width * w)
                height = int(bboxC.height * h)
                
                # Constrain to image bounds
                x = max(0, x)
                y = max(0, y)
                width = min(w - x, width)
                height = min(h - y, height)
                
                # Extract keypoints
                keypoints = {}
                if hasattr(detection.location_data, 'relative_keypoints'):
                    landmarks = detection.location_data.relative_keypoints
                    names = ['right_eye', 'left_eye', 'nose', 'mouth', 'right_ear', 'left_ear']
                    for i, lm in enumerate(landmarks):
                        if i < len(names):
                            keypoints[names[i]] = (int(lm.x * w), int(lm.y * h))
                
                results.append(DetectedFace(
                    bbox=(x, y, width, height),
                    confidence=detection.score[0],
                    keypoints=keypoints
                ))
                
        except Exception as e:
            logger.error(f"Error in face detection: {e}")
            
        return results
