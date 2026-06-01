from typing import List, Optional, Dict
import numpy as np
from database.db import db
from ai.face_recognizer import FaceRecognizer
from utils.logger import logger

class AuthService:
    def __init__(self, face_recognizer: FaceRecognizer):
        self.face_recognizer = face_recognizer
        
    def register_owner(self, name: str, face_images: List[np.ndarray], angle_metadata: Optional[List[str]] = None) -> bool:
        """Register the owner."""
        logger.info(f"Registering owner: {name}")
        return self.face_recognizer.register_owner(face_images, name, angle_metadata)
        
    def verify_owner(self, frame: np.ndarray) -> bool:
        """Verify the owner."""
        return self.face_recognizer.verify_owner(frame)
        
    def get_owner(self) -> Optional[Dict]:
        """Get owner info."""
        owner = db.get_owner()
        if owner:
            # Don't send embeddings to frontend
            if 'face_embedding' in owner:
                del owner['face_embedding']
        return owner
