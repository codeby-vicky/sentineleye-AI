from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Deque
from collections import deque
import time
import numpy as np

# Avoid circular imports by defining a minimal Face/Detection type for the tracker
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
    identity_history: Deque[str] = field(default_factory=lambda: deque(maxlen=5))
    is_active: bool = True
    missed_frames: int = 0
    
    @property
    def avg_gaze_score(self) -> float:
        if not self.gaze_history:
            return 0.0
        return sum(self.gaze_history) / len(self.gaze_history)

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
        detections format: [{'bbox': (x,y,w,h), 'identity': str, 'type': str, 'gaze_score': float}]
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
            best_iou = 0.2  # Minimum threshold
            best_det_idx = -1
            
            for det_idx in unassigned_detections:
                iou = self._calculate_iou(track.bbox, detections[det_idx]['bbox'])
                if iou > best_iou:
                    best_iou = iou
                    best_det_idx = det_idx
                    
            if best_det_idx != -1:
                # Update track
                det = detections[best_det_idx]
                track.bbox = det['bbox']
                track.last_seen = current_time
                track.persistence_seconds = current_time - track.first_seen
                track.missed_frames = 0
                
                if 'gaze_score' in det and det['gaze_score'] is not None:
                    track.gaze_history.append(det['gaze_score'])
                    
                track.identity_history.append(det['type'])
                
                # Temporal confidence for owner identity
                if track.identity_type == 'owner':
                    # Only downgrade from owner to unknown if at least 3 of last 5 frames agree it's unknown
                    unknown_count = sum(1 for t in track.identity_history if t == 'unknown')
                    if unknown_count >= 3:
                        track.identity = det['identity']
                        track.identity_type = det['type']
                else:
                    # Upgrade to owner immediately if detected
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
                
            self.tracks[self.next_id] = new_track
            self.next_id += 1
            
        # Deactivate old tracks
        for track in self.tracks.values():
            if track.missed_frames > self.max_missed_frames:
                track.is_active = False
                
        # Clean up very old inactive tracks to prevent memory leak
        to_delete = [tid for tid, t in self.tracks.items() if not t.is_active and current_time - t.last_seen > 10.0]
        for tid in to_delete:
            del self.tracks[tid]
            
        return [t for t in self.tracks.values() if t.is_active]
