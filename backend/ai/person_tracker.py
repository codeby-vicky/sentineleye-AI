from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Deque
from collections import deque
import time
import numpy as np

@dataclass
class TrackedPerson:
    track_id: int
    identity: str
    identity_type: str  # 'owner', 'trusted', 'unknown'
    bbox: Tuple[int, int, int, int]
    first_seen: float
    last_seen: float
    persistence_seconds: float = 0.0
    gaze_history: Deque[float] = field(default_factory=lambda: deque(maxlen=30))
    position_history: List[Tuple[int, int]] = field(default_factory=list)
    bbox_area_history: Deque[int] = field(default_factory=lambda: deque(maxlen=30))
    identity_history: Deque[str] = field(default_factory=lambda: deque(maxlen=10))
    confidence_history: Deque[float] = field(default_factory=lambda: deque(maxlen=10))
    is_active: bool = True
    missed_frames: int = 0
    
    @property
    def avg_gaze_score(self) -> float:
        if not self.gaze_history:
            return 0.0
        return sum(self.gaze_history) / len(self.gaze_history)
    
    @property
    def face_area(self) -> int:
        """Current face bounding box area."""
        return self.bbox[2] * self.bbox[3]
    
    @property
    def is_approaching(self) -> bool:
        """Check if the person's face is getting larger (approaching)."""
        if len(self.bbox_area_history) < 10:
            return False
        recent = list(self.bbox_area_history)
        first_half = sum(recent[:len(recent)//2]) / max(len(recent)//2, 1)
        second_half = sum(recent[len(recent)//2:]) / max(len(recent) - len(recent)//2, 1)
        return second_half > first_half * 1.15  # 15% growth = approaching

class PersonTracker:
    def __init__(self):
        self.tracks: Dict[int, TrackedPerson] = {}
        self.next_id = 1
        self.max_missed_frames = 15  # Approx 0.5 sec at 30fps
        
    def _calculate_iou(self, boxA: Tuple[int, int, int, int], boxB: Tuple[int, int, int, int]) -> float:
        """Calculate Intersection over Union for two bounding boxes (x, y, w, h)."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
        yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])
        
        interArea = max(0, xB - xA) * max(0, yB - yA)
        if interArea == 0:
            return 0.0
            
        boxAArea = boxA[2] * boxA[3]
        boxBArea = boxB[2] * boxB[3]
        
        iou = interArea / float(boxAArea + boxBArea - interArea)
        return iou

    def update(self, detections: List[dict], current_time: float) -> List[TrackedPerson]:
        """
        Update tracker with new detections.
        detections format: [{'bbox': (x,y,w,h), 'identity': str, 'type': str, 'confidence': float, 'gaze_score': float}]
        """
        # Increment missed frames for all active tracks
        for track in self.tracks.values():
            if track.is_active:
                track.missed_frames += 1
                
        # If no detections, deactivate old tracks
        if not detections:
            for track in self.tracks.values():
                if track.missed_frames > self.max_missed_frames:
                    track.is_active = False
            return [t for t in self.tracks.values() if t.is_active]
            
        unassigned_detections = list(range(len(detections)))
        unassigned_tracks = [tid for tid, t in self.tracks.items() if t.is_active]
        
        # Match detections to existing tracks using IoU
        for track_id in unassigned_tracks:
            track = self.tracks[track_id]
            best_iou = 0.2
            best_det_idx = -1
            
            for det_idx in unassigned_detections:
                iou = self._calculate_iou(track.bbox, detections[det_idx]['bbox'])
                if iou > best_iou:
                    best_iou = iou
                    best_det_idx = det_idx
                    
            if best_det_idx != -1:
                det = detections[best_det_idx]
                track.bbox = det['bbox']
                track.last_seen = current_time
                track.persistence_seconds = current_time - track.first_seen
                track.missed_frames = 0
                
                # Track face area for approach detection
                area = det['bbox'][2] * det['bbox'][3]
                track.bbox_area_history.append(area)
                
                if 'gaze_score' in det and det['gaze_score'] is not None:
                    track.gaze_history.append(det['gaze_score'])
                
                if 'confidence' in det:
                    track.confidence_history.append(det.get('confidence', 0.0))
                    
                track.identity_history.append(det['type'])
                
                # Temporal identity stability with voting
                if track.identity_type == 'owner':
                    # Only downgrade owner to unknown if 6 of last 10 frames say unknown
                    # This prevents momentary recognition failures from losing owner
                    unknown_count = sum(1 for t in track.identity_history if t == 'unknown')
                    if unknown_count >= 6:
                        track.identity = det['identity']
                        track.identity_type = det['type']
                else:
                    # Upgrade to owner immediately if detected with good confidence
                    if det['type'] == 'owner':
                        track.identity = det['identity']
                        track.identity_type = det['type']
                    else:
                        track.identity = det['identity']
                        track.identity_type = det['type']
                    
                x, y, w, h = det['bbox']
                centroid = (x + w//2, y + h//2)
                track.position_history.append(centroid)
                if len(track.position_history) > 30:
                    track.position_history.pop(0)
                    
                unassigned_detections.remove(best_det_idx)
                
        # Create new tracks for unassigned detections
        for det_idx in unassigned_detections:
            det = detections[det_idx]
            new_track = TrackedPerson(
                track_id=self.next_id,
                identity=det['identity'],
                identity_type=det['type'],
                bbox=det['bbox'],
                first_seen=current_time,
                last_seen=current_time
            )
            if 'gaze_score' in det and det['gaze_score'] is not None:
                new_track.gaze_history.append(det['gaze_score'])
            if 'confidence' in det:
                new_track.confidence_history.append(det.get('confidence', 0.0))
            
            # Initialize area tracking
            area = det['bbox'][2] * det['bbox'][3]
            new_track.bbox_area_history.append(area)
                
            self.tracks[self.next_id] = new_track
            self.next_id += 1
            
        # Deactivate old tracks
        for track in self.tracks.values():
            if track.missed_frames > self.max_missed_frames:
                track.is_active = False
                
        # Clean up very old inactive tracks
        to_delete = [tid for tid, t in self.tracks.items() if not t.is_active and current_time - t.last_seen > 10.0]
        for tid in to_delete:
            del self.tracks[tid]
            
        return [t for t in self.tracks.values() if t.is_active]
