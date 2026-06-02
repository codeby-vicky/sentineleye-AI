import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple, Dict
from utils.logger import logger
import os

class ObjectDetector:
    def __init__(self):
        logger.info("Initializing CPU-only YOLOv8n detector...")
        try:
            # Always force CPU to avoid the torchvision::nms CUDA crash on Windows
            self.model = YOLO('yolov8n.pt')
            # Run a dummy inference to warm up
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model(dummy, device='cpu', verbose=False)
            logger.info("YOLOv8n CPU initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize YOLO: {e}")
            self.model = None

    def detect(self, frame: np.ndarray) -> Dict[str, List[Tuple[int, int, int, int]]]:
        """
        Run YOLO detection and return bounding boxes for persons and cell phones.
        Returns: {'persons': [bbox1, bbox2], 'phones': [bbox]}
        bbox is (x, y, w, h)
        """
        results_dict = {'persons': [], 'phones': []}
        
        if self.model is None or frame is None:
            return results_dict

        try:
            # Force CPU
            results = self.model(frame, device='cpu', verbose=False, conf=0.4)
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # COCO class 0 is person, class 67 is cell phone
                    if cls_id == 0 or cls_id == 67:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        w = x2 - x1
                        h = y2 - y1
                        bbox = (x1, y1, w, h)
                        
                        if cls_id == 0:
                            results_dict['persons'].append(bbox)
                        elif cls_id == 67:
                            results_dict['phones'].append(bbox)
                            
        except Exception as e:
            logger.error(f"Error in YOLO detection: {e}")
            
        return results_dict

    def is_face_in_person(self, face_bbox: Tuple[int, int, int, int], person_bboxes: List[Tuple[int, int, int, int]]) -> bool:
        """Check if a face bounding box is inside any of the person bounding boxes."""
        if not person_bboxes:
            # If no persons detected by YOLO, we might be too close to the camera for a body detection.
            # We don't want to completely block face detection in that case, but we can be stricter.
            return True 
            
        fx, fy, fw, fh = face_bbox
        face_center_x = fx + fw // 2
        face_center_y = fy + fh // 2
        
        for px, py, pw, ph in person_bboxes:
            # Check if face center is within person bbox
            # We add a slight margin to person bbox
            if (px - 20 <= face_center_x <= px + pw + 20) and (py - 20 <= face_center_y <= py + ph + 20):
                return True
                
        return False
