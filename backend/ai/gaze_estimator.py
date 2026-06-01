import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass
from typing import Tuple, Optional
from utils.logger import logger
from config import Config

@dataclass
class GazeResult:
    gaze_direction: str  # 'toward_screen', 'away', 'peripheral'
    gaze_score: float    # 0.0 to 1.0
    head_angles: Tuple[float, float, float]  # pitch, yaw, roll
    landmarks: Optional[list] = None # List of (x, y) pixel coordinates

class GazeEstimator:
    def __init__(self):
        logger.info("Initializing MediaPipe Face Mesh for Gaze Estimation...")
        self.mp_face_mesh = mp.solutions.face_mesh
        # refine_landmarks=True is CRITICAL for iris tracking
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 3D generic model face points for solvePnP
        self.model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip (1)
            (0.0, -330.0, -65.0),        # Chin (152)
            (-225.0, 170.0, -135.0),     # Left eye left corner (33)
            (225.0, 170.0, -135.0),      # Right eye right corner (263)
            (-150.0, -150.0, -125.0),    # Left Mouth corner (61)
            (150.0, -150.0, -125.0)      # Right mouth corner (291)
        ])
        
    def estimate(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[GazeResult]:
        """Estimate head pose and gaze direction for a specific face."""
        x, y, w, h = bbox
        
        # Crop to face with some margin to improve face mesh performance
        margin = int(min(w, h) * 0.2)
        top = max(0, y - margin)
        bottom = min(frame.shape[0], y + h + margin)
        left = max(0, x - margin)
        right = min(frame.shape[1], x + w + margin)
        
        face_crop = frame[top:bottom, left:right]
        if face_crop.size == 0:
            return None
            
        # Convert BGR to RGB
        rgb_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        
        try:
            results = self.face_mesh.process(rgb_crop)
            
            if not results.multi_face_landmarks:
                return None
                
            landmarks = results.multi_face_landmarks[0]
            crop_h, crop_w, _ = face_crop.shape
            
            # Extract 2D points for PnP
            image_points = np.array([
                (landmarks.landmark[1].x * crop_w, landmarks.landmark[1].y * crop_h),     # Nose
                (landmarks.landmark[152].x * crop_w, landmarks.landmark[152].y * crop_h), # Chin
                (landmarks.landmark[33].x * crop_w, landmarks.landmark[33].y * crop_h),   # L eye
                (landmarks.landmark[263].x * crop_w, landmarks.landmark[263].y * crop_h), # R eye
                (landmarks.landmark[61].x * crop_w, landmarks.landmark[61].y * crop_h),   # L mouth
                (landmarks.landmark[291].x * crop_w, landmarks.landmark[291].y * crop_h)  # R mouth
            ], dtype="double")
            
            # Camera internals
            focal_length = crop_w
            center = (crop_w / 2, crop_h / 2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype="double")
            
            dist_coeffs = np.zeros((4, 1))
            
            # Solve PnP
            success, rotation_vector, translation_vector = cv2.solvePnP(
                self.model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            if not success:
                return None
                
            # Convert rotation vector to euler angles
            rmat, _ = cv2.Rodrigues(rotation_vector)
            angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
            
            pitch, yaw, roll = angles[0], angles[1], angles[2]
            
            # Simple gaze logic based on head pose
            # If head is looking forward (yaw close to 0) and slightly down/straight (pitch)
            is_looking_at_screen = (
                abs(yaw) < Config.GAZE_SCREEN_YAW_THRESHOLD and 
                -5 < pitch < Config.GAZE_SCREEN_PITCH_THRESHOLD
            )
            
            # Calculate a normalized score 0.0 to 1.0
            # 1.0 = dead center, 0.0 = completely away
            yaw_penalty = min(abs(yaw) / 30.0, 1.0)
            pitch_penalty = min(abs(pitch - 5) / 20.0, 1.0)
            
            score = 1.0 - (yaw_penalty * 0.6 + pitch_penalty * 0.4)
            score = max(0.0, min(1.0, score))
            
            direction = 'toward_screen' if is_looking_at_screen else 'away'
            if 0.3 < score < 0.6:
                direction = 'peripheral'
                
            # Extract all 478 landmarks to absolute pixel coordinates
            all_landmarks = []
            for lm in landmarks.landmark:
                all_landmarks.append((int(lm.x * crop_w + left), int(lm.y * crop_h + top)))
                
            return GazeResult(
                gaze_direction=direction,
                gaze_score=float(score),
                head_angles=(float(pitch), float(yaw), float(roll)),
                landmarks=all_landmarks
            )
            
        except Exception as e:
            logger.error(f"Error in gaze estimation: {e}")
            return None
