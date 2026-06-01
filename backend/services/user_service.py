from typing import List, Dict, Optional
import numpy as np
from database.db import db
from ai.face_recognizer import FaceRecognizer
from utils.logger import logger

class UserService:
    def __init__(self, face_recognizer: FaceRecognizer):
        self.face_recognizer = face_recognizer
        
    def add_trusted_user(self, name: str, relationship: str, face_images: List[np.ndarray]) -> Optional[int]:
        """Add a new trusted user."""
        logger.info(f"Adding trusted user: {name} ({relationship})")
        return self.face_recognizer.register_trusted_user(face_images, name, relationship)
        
    def get_trusted_users(self) -> List[Dict]:
        """Get list of all trusted users."""
        users = db.get_trusted_users()
        for u in users:
            if 'face_embedding' in u:
                del u['face_embedding']
        return users
        
    def remove_trusted_user(self, user_id: int) -> bool:
        """Remove a trusted user."""
        logger.info(f"Removing trusted user ID: {user_id}")
        success = db.delete_trusted_user(user_id)
        if success:
            self.face_recognizer.reload_embeddings()
        return success
