import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from utils.logger import logger
import os

@dataclass
class PhoneDetection:
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    orientation: str  # 'camera_facing', 'screen_facing', 'unknown'
    risk_level: str   # 'high', 'medium', 'low'

class ObjectDetector:
    # WHITELIST: Only these COCO classes are relevant for security
    PERSON_CLASS = 0
    PHONE_CLASS = 67
    ALLOWED_CLASSES = {0, 67}  # person, cell phone — everything else ignored
    
    def __init__(self):
        logger.info("Initializing YOLOv8n detector...")
        self._device = 'cpu'
        try:
            self.model = YOLO('yolov8n.pt')
            # Try GPU first
            try:
                import torch
                if torch.cuda.is_available():
                    dummy = np.zeros((640, 640, 3), dtype=np.uint8)
                    self.model(dummy, device='cuda:0', verbose=False)
                    self._device = 'cuda:0'
                    logger.info("YOLOv8n GPU (CUDA) initialized successfully.")
                else:
                    raise RuntimeError("No CUDA")
            except Exception as gpu_e:
                logger.warning(f"GPU init failed ({gpu_e}), falling back to CPU")
                dummy = np.zeros((640, 640, 3), dtype=np.uint8)
                self.model(dummy, device='cpu', verbose=False)
                self._device = 'cpu'
                logger.info("YOLOv8n CPU initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize YOLO: {e}")
            self.model = None

    def detect(self, frame: np.ndarray) -> Dict:
        """
        Run YOLO detection. Only returns persons and phones — all other objects ignored.
        Returns: {'persons': [bbox], 'phones': [PhoneDetection], 'raw_phone_bboxes': [bbox]}
        """
        results_dict = {'persons': [], 'phones': [], 'raw_phone_bboxes': []}
        
        if self.model is None or frame is None:
            return results_dict

        try:
            # Use classes filter to only detect person (0) and phone (67)
            results = self.model(
                frame, 
                device=self._device, 
                verbose=False, 
                conf=0.25,
                classes=[self.PERSON_CLASS, self.PHONE_CLASS]
            )
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    w = x2 - x1
                    h = y2 - y1
                    bbox = (x1, y1, w, h)
                    
                    if cls_id == self.PERSON_CLASS and conf >= 0.4:
                        results_dict['persons'].append(bbox)
                    elif cls_id == self.PHONE_CLASS and conf >= 0.25:
                        orientation = self._estimate_phone_orientation(bbox, frame)
                        risk = self._calculate_phone_risk(orientation, conf)
                        
                        phone_det = PhoneDetection(
                            bbox=bbox,
                            confidence=conf,
                            orientation=orientation,
                            risk_level=risk
                        )
                        results_dict['phones'].append(phone_det)
                        results_dict['raw_phone_bboxes'].append(bbox)
                            
        except Exception as e:
            logger.error(f"Error in YOLO detection: {e}")
            # Fall back to CPU if GPU fails mid-session
            if self._device != 'cpu':
                logger.warning("Falling back to CPU for YOLO")
                self._device = 'cpu'
            
        return results_dict

    def _estimate_phone_orientation(self, bbox: Tuple[int, int, int, int], frame: np.ndarray) -> str:
        """Estimate phone camera orientation using visual analysis."""
        x, y, w, h = bbox
        
        # Crop the phone region
        pad = 5
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(frame.shape[1], x + w + pad)
        y2 = min(frame.shape[0], y + h + pad)
        phone_crop = frame[y1:y2, x1:x2]
        
        if phone_crop.size == 0:
            return 'unknown'
        
        gray = cv2.cvtColor(phone_crop, cv2.COLOR_BGR2GRAY)
        
        # Check for dark circular features (camera lens on back)
        _, dark_mask = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY_INV)
        dark_ratio = np.sum(dark_mask > 0) / max(dark_mask.size, 1)
        
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=10,
            param1=100, param2=30,
            minRadius=2, maxRadius=max(w, h) // 4
        )
        
        has_lens_pattern = circles is not None and len(circles[0]) >= 1
        
        if has_lens_pattern and dark_ratio > 0.05:
            return 'camera_facing'
        elif dark_ratio < 0.02:
            return 'screen_facing'
        else:
            return 'unknown'
    
    def _calculate_phone_risk(self, orientation: str, confidence: float) -> str:
        """Calculate risk level based on phone orientation and detection confidence."""
        if orientation == 'camera_facing':
            return 'high'
        elif orientation == 'unknown':
            return 'medium' if confidence > 0.4 else 'low'
        else:
            return 'low'

    def is_face_in_person(self, face_bbox: Tuple[int, int, int, int], person_bboxes: List[Tuple[int, int, int, int]]) -> bool:
        """Check if a face bounding box is inside any person bounding box."""
        if not person_bboxes:
            return True  # No person detected = close to camera
            
        fx, fy, fw, fh = face_bbox
        face_center_x = fx + fw // 2
        face_center_y = fy + fh // 2
        
        for px, py, pw, ph in person_bboxes:
            if (px - 40 <= face_center_x <= px + pw + 40) and (py - 40 <= face_center_y <= py + ph + 40):
                return True
                
        return False
    
    def is_phone_near_person(self, phone_bbox: Tuple[int, int, int, int], 
                              person_bboxes: List[Tuple[int, int, int, int]],
                              frame_width: int) -> bool:
        """Check if a phone is near a person."""
        if not person_bboxes:
            return True
            
        px_phone, py_phone, pw_phone, ph_phone = phone_bbox
        phone_cx = px_phone + pw_phone // 2
        phone_cy = py_phone + ph_phone // 2
        
        for px, py, pw, ph in person_bboxes:
            margin = int(frame_width * 0.05)
            if (px - margin <= phone_cx <= px + pw + margin) and \
               (py - margin <= phone_cy <= py + ph + margin):
                return True
                
        return False

    def get_phone_owner_association(self, phone_bbox: Tuple[int, int, int, int],
                                     owner_person_bbox: Optional[Tuple[int, int, int, int]],
                                     other_person_bboxes: List[Tuple[int, int, int, int]],
                                     frame_width: int) -> str:
        """
        Determine who is holding the phone.
        Returns: 'owner', 'unknown', 'none' (not near any person)
        """
        if phone_bbox is None:
            return 'none'
            
        px, py, pw, ph = phone_bbox
        phone_cx = px + pw // 2
        phone_cy = py + ph // 2
        margin = int(frame_width * 0.08)
        
        # Check if phone is inside owner's person bbox
        if owner_person_bbox:
            ox, oy, ow, oh = owner_person_bbox
            if (ox - margin <= phone_cx <= ox + ow + margin) and \
               (oy - margin <= phone_cy <= oy + oh + margin):
                return 'owner'
        
        # Check if phone is inside any other person's bbox
        for pbbox in other_person_bboxes:
            ux, uy, uw, uh = pbbox
            if (ux - margin <= phone_cx <= ux + uw + margin) and \
               (uy - margin <= phone_cy <= uy + uh + margin):
                return 'unknown'
        
        return 'none'
