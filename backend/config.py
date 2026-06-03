import os

class Config:
    # Camera settings
    CAMERA_RESOLUTION = (1920, 1080)
    CAMERA_INDEX = 0
    
    # Face recognition - dlib fallback
    FACE_RECOGNITION_THRESHOLD = 0.6
    
    # Face recognition - InsightFace (cosine similarity, higher = more similar)
    INSIGHTFACE_THRESHOLD = 0.35
    INSIGHTFACE_MODEL = 'buffalo_l'
    
    # Gaze estimation
    GAZE_SCREEN_YAW_THRESHOLD = 15 # degrees
    GAZE_SCREEN_PITCH_THRESHOLD = 10 # degrees
    
    # Motion and crossing
    CROSSING_MAX_DURATION = 3.0 # seconds
    CROSSING_MIN_FRAME_TRAVEL = 0.6 # 60% of frame width
    
    # Screen analysis
    OCR_INTERVAL_SECONDS = 5
    
    # Threat calculation weights
    THREAT_WEIGHTS = {
        'observer_identity': 0.25,
        'gaze_toward_screen': 0.20,
        'persistence_duration': 0.15,
        'screen_sensitivity': 0.20,
        'observer_count': 0.10,
        'behavior_anomaly': 0.10
    }
    
    # Threat level thresholds
    THREAT_LEVEL_THRESHOLDS = {
        'LOW': 15,
        'MEDIUM': 35,
        'HIGH': 60,
        'CRITICAL': 80
    }
    
    # Multipliers
    TRUSTED_PERSON_DISCOUNT = 0.4
    CROSSING_DISCOUNT = 0.2
    
    # Frame scheduling intervals (in frame counts at ~30fps)
    SCHEDULE_FACE_DETECT = 1     # Every frame
    SCHEDULE_GAZE = 1            # Every frame
    SCHEDULE_YOLO = 3            # Every 3rd frame (~100ms)
    SCHEDULE_FACE_RECOGNIZE = 5  # Every 5th frame (~165ms)
    SCHEDULE_OCR = 150           # Every 150 frames (~5s)
    SCHEDULE_NLP = 300           # Every 300 frames (~10s)
    
    # Project paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    DATABASE_PATH = os.path.join(DATA_DIR, 'sentineleye.db')
    LOGS_DIR = os.path.join(DATA_DIR, 'logs')
    EMBEDDINGS_DIR = os.path.join(DATA_DIR, 'embeddings')
    CAPTURES_DIR = os.path.join(DATA_DIR, 'captures')
    
    # Default settings
    SOUND_ALERTS_ENABLED = True

    @classmethod
    def init_app(cls):
        # Create directories if they don't exist
        for directory in [cls.DATA_DIR, cls.LOGS_DIR, cls.EMBEDDINGS_DIR, cls.CAPTURES_DIR]:
            os.makedirs(directory, exist_ok=True)
