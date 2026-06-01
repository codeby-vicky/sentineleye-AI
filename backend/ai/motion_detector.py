import cv2
import numpy as np
import time
from dataclasses import dataclass
from typing import List, Tuple
from config import Config

@dataclass
class MotionBlob:
    id: int
    centroid: Tuple[int, int]
    area: float
    bbox: Tuple[int, int, int, int]
    first_seen: float
    last_seen: float
    path: List[Tuple[int, int]]
    
class MotionDetector:
    def __init__(self):
        # MOG2 Background subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=25, detectShadows=True
        )
        self.blobs = {}
        self.next_blob_id = 1
        self.min_area = 5000  # Minimum size for a person
        
    def detect_motion(self, frame: np.ndarray) -> List[MotionBlob]:
        """Detect moving blobs and track them to identify crossing events."""
        if frame is None:
            return []
            
        current_time = time.time()
        
        # Apply background subtraction
        # Downscale for performance
        small_frame = cv2.resize(frame, (640, 360))
        fg_mask = self.bg_subtractor.apply(small_frame)
        
        # Remove shadows (MOG2 marks shadows as 127)
        _, fg_mask = cv2.threshold(fg_mask, 254, 255, cv2.THRESH_BINARY)
        
        # Morphological operations to remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        current_blobs = []
        h, w = small_frame.shape[:2]
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area:
                continue
                
            x, y, cw, ch = cv2.boundingRect(contour)
            cx, cy = x + cw // 2, y + ch // 2
            
            # Scale coordinates back to original frame size
            scale_x = frame.shape[1] / w
            scale_y = frame.shape[0] / h
            
            orig_bbox = (int(x * scale_x), int(y * scale_y), int(cw * scale_x), int(ch * scale_y))
            orig_centroid = (int(cx * scale_x), int(cy * scale_y))
            orig_area = area * scale_x * scale_y
            
            current_blobs.append((orig_centroid, orig_area, orig_bbox))
            
        self._update_tracks(current_blobs, current_time)
        self._cleanup_old_tracks(current_time)
        
        return list(self.blobs.values())
        
    def _update_tracks(self, current_blobs: List[Tuple], current_time: float):
        """Match new blobs to existing tracks using simple nearest neighbor."""
        unassigned_blobs = list(current_blobs)
        
        for blob_id, blob in self.blobs.items():
            if not unassigned_blobs:
                break
                
            # Find closest new blob
            min_dist = float('inf')
            best_match_idx = -1
            
            for i, (centroid, _, _) in enumerate(unassigned_blobs):
                dist = np.sqrt((blob.centroid[0] - centroid[0])**2 + (blob.centroid[1] - centroid[1])**2)
                if dist < min_dist and dist < 150:  # Max pixel movement per frame
                    min_dist = dist
                    best_match_idx = i
                    
            if best_match_idx >= 0:
                # Update existing blob
                matched = unassigned_blobs.pop(best_match_idx)
                blob.centroid = matched[0]
                blob.area = matched[1]
                blob.bbox = matched[2]
                blob.last_seen = current_time
                blob.path.append(matched[0])
                if len(blob.path) > 30:  # Keep path history bounded
                    blob.path.pop(0)
                    
        # Create new tracks for unassigned blobs
        for centroid, area, bbox in unassigned_blobs:
            self.blobs[self.next_blob_id] = MotionBlob(
                id=self.next_blob_id,
                centroid=centroid,
                area=area,
                bbox=bbox,
                first_seen=current_time,
                last_seen=current_time,
                path=[centroid]
            )
            self.next_blob_id += 1
            
    def _cleanup_old_tracks(self, current_time: float):
        """Remove tracks that haven't been seen recently."""
        # Remove if not seen for 1 second
        to_delete = [blob_id for blob_id, blob in self.blobs.items() 
                    if current_time - blob.last_seen > 1.0]
        for blob_id in to_delete:
            del self.blobs[blob_id]
            
    def is_crossing(self, frame_width: int, current_time: float) -> bool:
        """
        Evaluate all current tracks to see if any constitute a 'crossing' event.
        A crossing is fast horizontal movement across the screen.
        """
        min_travel = frame_width * Config.CROSSING_MIN_FRAME_TRAVEL
        max_duration = Config.CROSSING_MAX_DURATION
        
        for blob in self.blobs.values():
            if len(blob.path) < 5:
                continue
                
            # Calculate total horizontal travel
            x_coords = [p[0] for p in blob.path]
            min_x, max_x = min(x_coords), max(x_coords)
            horizontal_travel = max_x - min_x
            
            duration = current_time - blob.first_seen
            
            # If it travelled far enough, fast enough
            if horizontal_travel > min_travel and duration < max_duration:
                # To prevent spamming, reset this blob's path so it doesn't trigger again immediately
                blob.path = [blob.centroid]
                blob.first_seen = current_time
                return True
                
        return False
