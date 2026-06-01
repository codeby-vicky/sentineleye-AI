import numpy as np
import os
os.environ['TORCH_FORCE_WEIGHTS_ONLY_LOAD'] = '0'
from ultralytics import YOLO
from typing import Tuple, List, Dict
from utils.logger import logger

class YoloDetector:
    def __init__(self):
        logger.info("Initializing YOLOv8n detector...")
        try:
            # Load the nano model (downloads automatically if not present)
            self.model = YOLO('yolov8n.pt')
            logger.info("YOLOv8n loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading YOLO model: {e}")
            self.model = None

    def detect(self, frame: np.ndarray) -> Tuple[List[Dict], List[Dict]]:
        """
        Detects persons and cell phones in the frame.
        Returns (persons, phones) where each is a list of dicts: {'bbox': (x,y,w,h), 'conf': float}
        """
        persons = []
        phones = []
        
        if self.model is None or frame is None:
            return persons, phones
            
        try:
            # Classes: 0 is person, 67 is cell phone in COCO
            results = self.model(frame, classes=[0, 67], conf=0.35, verbose=False)
            
            if len(results) > 0:
                boxes = results[0].boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    
                    # Ensure coordinates are within frame bounds and valid width/height
                    w = max(0, x2 - x1)
                    h = max(0, y2 - y1)
                    
                    if w > 0 and h > 0:
                        bbox = (x1, y1, w, h)
                        if cls_id == 0:
                            persons.append({'bbox': bbox, 'conf': conf})
                        elif cls_id == 67:
                            phones.append({'bbox': bbox, 'conf': conf})
                            
        except Exception as e:
            logger.error(f"Error in YOLO detection: {e}")
            
        return persons, phones
