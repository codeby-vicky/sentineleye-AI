import cv2
import numpy as np
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
        self.owner = None
        self._use_insightface = False
        self._insightface_app = None
        self._fallback_threshold = Config.FACE_RECOGNITION_THRESHOLD
        self._insightface_threshold = Config.INSIGHTFACE_THRESHOLD
        
        # Try InsightFace first (better accuracy, GPU-accelerated)
        try:
            import insightface
            from insightface.app import FaceAnalysis
            logger.info("Loading InsightFace buffalo_l model...")
            self._insightface_app = FaceAnalysis(
                name=Config.INSIGHTFACE_MODEL,
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            self._insightface_app.prepare(ctx_id=0, det_size=(640, 640))
            self._use_insightface = True
            logger.info("InsightFace initialized successfully (GPU-accelerated)")
        except Exception as e:
            logger.warning(f"InsightFace not available ({e}), falling back to face_recognition (dlib)")
            self._use_insightface = False
        
        self.reload_embeddings()
        self._initialized = True
        
    def reload_embeddings(self):
        """Reload all embeddings from the database."""
        logger.info("Reloading face embeddings from database...")
        self.owner = db.get_owner()
        if self.owner and self.owner.get('face_embedding') is None:
            logger.warning("Owner loaded but embedding is None. Acting as if no owner exists.")
            self.owner = None
        logger.info(f"Loaded owner: {'Yes' if self.owner else 'No'}")
        if self.owner:
            emb = self.owner['face_embedding']
            if emb.ndim == 1:
                logger.info(f"  Owner embeddings: 1 (dim={emb.shape[0]})")
            else:
                logger.info(f"  Owner embeddings: {emb.shape[0]} (dim={emb.shape[1]})")

    def _get_embedding_insightface(self, frame: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """Extract face embedding using InsightFace."""
        if self._insightface_app is None:
            return None
            
        try:
            if bbox is not None:
                x, y, w, h = bbox
                # Expand crop for better face analysis
                margin_x = int(w * 0.3)
                margin_y = int(h * 0.3)
                x1 = max(0, x - margin_x)
                y1 = max(0, y - margin_y)
                x2 = min(frame.shape[1], x + w + margin_x)
                y2 = min(frame.shape[0], y + h + margin_y)
                crop = frame[y1:y2, x1:x2]
                if crop.size == 0:
                    return None
            else:
                crop = frame
                
            faces = self._insightface_app.get(crop)
            if not faces:
                return None
            
            # If we provided a bbox, find the face closest to center of crop
            if bbox is not None and len(faces) > 1:
                crop_h, crop_w = crop.shape[:2]
                center = np.array([crop_w / 2, crop_h / 2])
                best_face = min(faces, key=lambda f: np.linalg.norm(
                    np.array([(f.bbox[0] + f.bbox[2]) / 2, (f.bbox[1] + f.bbox[3]) / 2]) - center
                ))
                return best_face.normed_embedding
            
            return faces[0].normed_embedding
            
        except Exception as e:
            logger.error(f"InsightFace embedding error: {e}")
            return None

    def _get_embedding_dlib(self, frame: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """Extract face embedding using dlib/face_recognition (fallback)."""
        try:
            import face_recognition
        except ImportError:
            logger.error("face_recognition not installed")
            return None
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        locations = None
        if bbox is not None:
            x, y, w, h = bbox
            top = max(0, y)
            right = min(frame.shape[1], x + w)
            bottom = min(frame.shape[0], y + h)
            left = max(0, x)
            locations = [(top, right, bottom, left)]
            
        try:
            encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=locations)
            if not encodings:
                return None
            return encodings[0]
        except Exception as e:
            logger.error(f"Error extracting dlib embedding: {e}")
            return None

    def _get_embedding(self, frame: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """Extract face embedding using best available backend."""
        if self._use_insightface:
            emb = self._get_embedding_insightface(frame, bbox)
            if emb is not None:
                return emb
            # Fall through to dlib if InsightFace fails for this frame
            
        return self._get_embedding_dlib(frame, bbox)

    def _compare_embeddings(self, emb: np.ndarray, stored_embeddings: np.ndarray) -> float:
        """
        Compare embedding against stored embeddings.
        Returns: distance (lower = more similar) for dlib, or similarity score for InsightFace.
        For consistency, we return a 'confidence' score (0.0 to 1.0, higher = better match).
        """
        if stored_embeddings.ndim == 1:
            stored_embeddings = stored_embeddings.reshape(1, -1)
        
        # Check if dimensions match
        if emb.shape[0] != stored_embeddings.shape[1]:
            return 0.0
            
        if self._use_insightface and emb.shape[0] == 512:
            # Cosine similarity for InsightFace (512-d normalized)
            similarities = np.dot(stored_embeddings, emb)
            max_sim = float(np.max(similarities))
            return max_sim  # Already 0-1 range for normalized vectors
        else:
            # Euclidean distance for dlib (128-d)
            import face_recognition
            distances = face_recognition.face_distance(stored_embeddings, emb)
            min_dist = float(np.min(distances))
            return max(0.0, 1.0 - min_dist)  # Convert to confidence

    def register_owner(self, frames: List[np.ndarray], name: str, angle_metadata: Optional[List[str]] = None) -> bool:
        """Register the owner by storing embeddings from multiple frames and angles."""
        embeddings = []
        for i, frame in enumerate(frames):
            emb = self._get_embedding(frame)
            if emb is not None:
                embeddings.append(emb)
                angle = angle_metadata[i] if angle_metadata and i < len(angle_metadata) else f"frame_{i}"
                logger.info(f"  Extracted embedding for angle: {angle} (dim={emb.shape[0]})")
                
        if not embeddings:
            logger.error("Could not extract any faces for owner registration")
            return False
        
        # Validate embedding quality - remove outliers
        if len(embeddings) > 3:
            embeddings = self._filter_outlier_embeddings(embeddings)
            
        embeddings_array = np.array(embeddings)
        logger.info(f"Storing {len(embeddings)} embeddings (dim={embeddings_array.shape[1]})")
        
        success = db.set_owner(name, embeddings_array)
        if success:
            self.reload_embeddings()
        return success

    def _filter_outlier_embeddings(self, embeddings: List[np.ndarray]) -> List[np.ndarray]:
        """Remove embeddings that are too different from the group (likely bad captures)."""
        if len(embeddings) <= 3:
            return embeddings
            
        arr = np.array(embeddings)
        # Calculate pairwise cosine similarities
        mean_emb = arr.mean(axis=0)
        mean_emb = mean_emb / (np.linalg.norm(mean_emb) + 1e-8)
        
        similarities = []
        for emb in arr:
            norm_emb = emb / (np.linalg.norm(emb) + 1e-8)
            sim = float(np.dot(norm_emb, mean_emb))
            similarities.append(sim)
        
        # Keep embeddings with similarity > 0.5 to the mean
        filtered = [emb for emb, sim in zip(embeddings, similarities) if sim > 0.5]
        
        if len(filtered) < 3:
            return embeddings  # Don't filter too aggressively
            
        logger.info(f"Filtered {len(embeddings) - len(filtered)} outlier embeddings")
        return filtered

    def verify_owner(self, frame: np.ndarray) -> bool:
        """Quick verification check against owner only."""
        if not self.owner:
            return False
            
        emb = self._get_embedding(frame)
        if emb is None:
            return False
            
        confidence = self._compare_embeddings(emb, self.owner['face_embedding'])
        
        if self._use_insightface:
            return confidence > self._insightface_threshold
        else:
            return confidence > (1.0 - self._fallback_threshold)

    def identify(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Tuple[str, str, float]:
        """
        Identify a face in a frame given its bounding box.
        Returns: (name, type, confidence)
        type is 'owner' or 'unknown'
        """
        emb = self._get_embedding(frame, bbox)
        if emb is None:
            return "Unknown", "unknown", 0.0
            
        # Check owner
        if self.owner:
            stored_emb = self.owner['face_embedding']
            stored_dim = stored_emb.shape[-1]
            
            confidence = self._compare_embeddings(emb, stored_emb)
            
            # If dimension mismatch (InsightFace 512-d vs stored 128-d), fall back to dlib
            if confidence == 0.0 and emb.shape[0] != stored_dim and self._use_insightface:
                dlib_emb = self._get_embedding_dlib(frame, bbox)
                if dlib_emb is not None:
                    confidence = self._compare_embeddings(dlib_emb, stored_emb)
                    # Use dlib threshold for this comparison
                    threshold = 1.0 - self._fallback_threshold
                    if confidence > threshold:
                        return self.owner['name'], "owner", float(confidence)
                    return "Unknown", "unknown", 0.0
            
            if self._use_insightface and emb.shape[0] == 512:
                threshold = self._insightface_threshold
            else:
                threshold = 1.0 - self._fallback_threshold
            
            if confidence > threshold:
                return self.owner['name'], "owner", float(confidence)

        return "Unknown", "unknown", 0.0

