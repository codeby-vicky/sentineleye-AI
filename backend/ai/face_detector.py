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
            min_detection_confidence=0.40  # Increased for stable owner tracking (less false face drift)
        )
        
        # Fallback cascade for extreme side profiles that MediaPipe might miss
        cascade_path = cv2.data.haarcascades + 'haarcascade_profileface.xml'
        self.profile_cascade = cv2.CascadeClassifier(cascade_path)
        logger.info("Loaded profile face cascade fallback.")
        
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
            
        # PASS 2: Detect extreme side profiles (left and right) using Haar Cascade
        # We only add them if they don't heavily overlap with MediaPipe detections
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Detect right-facing profiles
            profiles_right = self.profile_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
            # Detect left-facing profiles (flip image)
            gray_flipped = cv2.flip(gray, 1)
            profiles_left_flipped = self.profile_cascade.detectMultiScale(gray_flipped, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
            
            new_bboxes = []
            if len(profiles_right) > 0:
                new_bboxes.extend([(x, y, w, h) for (x, y, w, h) in profiles_right])
                
            if len(profiles_left_flipped) > 0:
                for (fx, fy, fw, fh) in profiles_left_flipped:
                    # Unflip coordinates
                    x = w - (fx + fw)
                    new_bboxes.append((x, fy, fw, fh))
                    
            # Filter overlaps
            for nx, ny, nw, nh in new_bboxes:
                is_overlap = False
                for existing in results:
                    ex, ey, ew, eh = existing.bbox
                    # Calculate IoU roughly
                    inter_x = max(nx, ex)
                    inter_y = max(ny, ey)
                    inter_w = min(nx+nw, ex+ew) - inter_x
                    inter_h = min(ny+nh, ey+eh) - inter_y
                    
                    if inter_w > 0 and inter_h > 0:
                        inter_area = inter_w * inter_h
                        area_n = nw * nh
                        area_e = ew * eh
                        iou = inter_area / float(area_n + area_e - inter_area)
                        if iou > 0.3:  # Significant overlap
                            is_overlap = True
                            break
                            
                if not is_overlap:
                    results.append(DetectedFace(
                        bbox=(nx, ny, nw, nh),
                        confidence=0.5, # Default confidence for cascade
                        keypoints={} # No keypoints for cascade
                    ))
                    
        except Exception as e:
            logger.warning(f"Profile cascade fallback failed: {e}")
            
        return results
