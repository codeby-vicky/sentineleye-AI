from dataclasses import dataclass
from typing import Optional, List
import numpy as np

@dataclass
class Owner:
    id: int
    name: str
    face_embedding: np.ndarray
    created_at: str
    updated_at: str
    is_active: bool

@dataclass
class TrustedUser:
    id: int
    name: str
    relationship: str
    face_embedding: np.ndarray
    trust_level: float
    created_at: str
    is_active: bool

@dataclass
class DetectionEvent:
    id: int
    session_id: int
    timestamp: str
    observer_type: str
    observer_id: Optional[int]
    observer_name: Optional[str]
    gaze_score: float
    persistence_seconds: float
    screen_sensitivity: str
    threat_score: float
    threat_level: str
    action_taken: str
    reason: str

@dataclass
class Session:
    id: int
    start_time: str
    end_time: Optional[str]
    total_detections: int
    unknown_count: int
    trusted_count: int
    crossing_count: int
    high_risk_count: int
    avg_threat_score: float

@dataclass
class Setting:
    id: int
    key: str
    value: str
    category: str
    updated_at: str

@dataclass
class AlertLog:
    id: int
    timestamp: str
    detection_event_id: int
    alert_type: str
    message: str
    acknowledged: bool
