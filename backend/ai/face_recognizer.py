import cv2
import numpy as np
import face_recognition
from typing import List, Tuple, Optional, Dict
from database.db import db
from config import Config
from utils.logger import logger

class FaceRecognizer:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(FaceRecognizer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        logger.info("Initializing Face Recognizer...")
        self.threshold = Config.FACE_RECOGNITION_THRESHOLD
        self.owner = None
        self.reload_embeddings()
        self._initialized = True
        
    def reload_embeddings(self):
        """Reload all embeddings from the database."""
        logger.info("Reloading face embeddings from database...")
        self.owner = db.get_owner()
        if self.owner and self.owner.get('face_embedding') is None:
            logger.warning("Owner loaded but embedding is None (likely corrupted). Acting as if no owner exists.")
            self.owner = None
        logger.info(f"Loaded owner: {'Yes' if self.owner else 'No'}")

    def _get_embedding(self, frame: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """Extract a 128-d face embedding from an image frame."""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        locations = None
        if bbox is not None:
            # face_recognition uses (top, right, bottom, left)
            x, y, w, h = bbox
            # Constrain to frame bounds
            top = max(0, y)
            right = min(frame.shape[1], x + w)
            bottom = min(frame.shape[0], y + h)
            left = max(0, x)
            locations = [(top, right, bottom, left)]
            
        try:
            # Extract embedding
            encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=locations)
            if not encodings:
                return None
            return encodings[0]
        except Exception as e:
            logger.error(f"Error extracting embedding: {e}")
            return None

    def register_owner(self, frames: List[np.ndarray], name: str, angle_metadata: Optional[List[str]] = None) -> bool:
        """Register the owner by storing embeddings from multiple frames and angles."""
        embeddings = []
        for frame in frames:
            emb = self._get_embedding(frame)
            if emb is not None:
                embeddings.append(emb)
                
        if not embeddings:
            logger.error("Could not extract any faces for owner registration")
            return False
            
        # Store as a 2D numpy array (N, 128)
        embeddings_array = np.array(embeddings)
        
        success = db.set_owner(name, embeddings_array)
        if success:
            self.reload_embeddings()
        return success


    def verify_owner(self, frame: np.ndarray) -> bool:
        """Quick verification check against owner only."""
        if not self.owner:
            return False
            
        emb = self._get_embedding(frame)
        if emb is None:
            return False
        owner_embeddings = self.owner['face_embedding']
        # If it's a 1D array (old format), wrap it in a list. Otherwise it's already iterable
        if owner_embeddings.ndim == 1:
            owner_embeddings = [owner_embeddings]
            
        distances = face_recognition.face_distance(owner_embeddings, emb)
        min_distance = min(distances) if len(distances) > 0 else 1.0
        return min_distance < self.threshold

    def identify(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Tuple[str, str, float]:
        """
        Identify a face in a frame given its bounding box.
        Returns: (name, type, distance)
        type is 'owner', 'trusted', or 'unknown'
        """
        emb = self._get_embedding(frame, bbox)
        if emb is None:
            return "Unknown", "unknown", 1.0
            
        # Check owner first
        if self.owner:
            owner_embeddings = self.owner['face_embedding']
            if owner_embeddings.ndim == 1:
                owner_embeddings = [owner_embeddings]
                
            distances = face_recognition.face_distance(owner_embeddings, emb)
            min_dist = min(distances) if len(distances) > 0 else 1.0
            
            if min_dist < self.threshold:
                confidence = max(0.0, 1.0 - float(min_dist))
                return self.owner['name'], "owner", confidence
                

        # No match found
        return "Unknown", "unknown", 0.0
