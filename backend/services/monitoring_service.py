import threading
import time
import cv2
import traceback
import numpy as np
from typing import Dict, Any, Optional
from database.db import db
from config import Config
from utils.logger import logger

from ai.camera_manager import CameraManager
# Heavy imports moved to _init_modules for lazy loading

from risk_engine.threat_calculator import ThreatCalculator, ObserverData
from risk_engine.behavior_analyzer import BehaviorAnalyzer
from risk_engine.decision_engine import DecisionEngine

from services.defense_service import DefenseService


class MonitoringService:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MonitoringService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self, socketio=None):
        if self._initialized:
            if socketio and not self.socketio:
                self.socketio = socketio
                if self.defense_service:
                    self.defense_service.alert_manager.socketio = socketio
                    self.defense_service.screen_blur.socketio = socketio
            return
            
        logger.info("Initializing Monitoring Service...")
        self.socketio = socketio
        self.is_running = False
        self.thread = None
        self.session_id = None
        self.last_ocr_time = 0
        self.current_sensitivity = 'safe'
        self.current_threat_score = 0.0
        self.current_threat_level = 'LOW'
        self.current_window_title = ""
        
        # Stats
        self.stats = {
            'total_detections': 0,
            'unknown_count': 0,
            'trusted_count': 0,
            'crossing_count': 0,
            'high_risk_count': 0,
            'sum_threat_score': 0.0,
            'threat_updates': 0
        }
        
        # Lazy initialization of AI modules
        self.camera = CameraManager()
        self.face_detector = None
        self.face_recognizer = None
        self.gaze_estimator = None
        self.motion_detector = None
        self.person_tracker = None
        self.yolo_detector = None
        
        self.screen_capture = None
        self.text_extractor = None
        self.sensitivity_classifier = None
        self.context_analyzer = None
        
        self.threat_calculator = None
        self.behavior_analyzer = None
        self.decision_engine = None
        self.defense_service = None
        
        self.last_frame = None
        self.last_annotated_frame = None
        self.last_detections = []
        
        self._initialized = True
        
    def _init_modules(self):
        """Initialize AI modules only when monitoring starts."""
        if self.face_detector is None:
            logger.info("Loading AI modules...")
            
            try:
                from ai.face_detector import FaceDetector
                from ai.face_recognizer import FaceRecognizer
                from ai.gaze_estimator import GazeEstimator
                from ai.person_tracker import PersonTracker
                from ai.yolo_detector import YoloDetector
                self.face_detector = FaceDetector()
                self.face_recognizer = FaceRecognizer()
                self.gaze_estimator = GazeEstimator()
                self.person_tracker = PersonTracker()
                self.yolo_detector = YoloDetector()
            except Exception as e:
                logger.error(f"Error loading core CV modules: {e}")
                
            try:
                from ai.motion_detector import MotionDetector
                self.motion_detector = MotionDetector()
            except Exception as e:
                logger.error(f"Error loading motion detector: {e}")
            
            try:
                from ocr.screen_capture import ScreenCapture
                from ocr.text_extractor import TextExtractor
                self.screen_capture = ScreenCapture()
                self.text_extractor = TextExtractor()
            except Exception as e:
                logger.error(f"Error loading OCR modules: {e}")
                
            try:
                from nlp.sensitivity_classifier import SensitivityClassifier
                from nlp.context_analyzer import ContextAnalyzer
                self.sensitivity_classifier = SensitivityClassifier()
                self.context_analyzer = ContextAnalyzer()
            except Exception as e:
                logger.error(f"Error loading NLP modules: {e}")
            
            self.threat_calculator = ThreatCalculator()
            self.behavior_analyzer = BehaviorAnalyzer()
            self.decision_engine = DecisionEngine()
            self.defense_service = DefenseService(self.socketio)
            logger.info("AI modules loading attempt finished.")
            
    def start_session(self) -> int:
        if self.is_running:
            logger.warning("Monitoring already running.")
            return self.session_id
            
        self._init_modules()
        
        # Load settings
        settings = db.get_all_settings()
        camera_index = int(settings.get('camera_index', '0'))
        
        if not self.camera.open(camera_index, Config.CAMERA_RESOLUTION):
            logger.error("Failed to start monitoring: Camera could not be opened.")
            return -1
            
        self.session_id = db.create_session()
        self.is_running = True
        
        # Reset stats
        for k in self.stats:
            self.stats[k] = 0
            
        self.thread = self.socketio.start_background_task(self._monitoring_loop)
        
        logger.info(f"Started monitoring session {self.session_id}")
        if self.socketio:
            self.socketio.emit('status_update', self.get_status())
            
        return self.session_id
        
    def stop_session(self):
        if not self.is_running:
            return
            
        logger.info(f"Stopping monitoring session {self.session_id}")
        self.is_running = False
        self.thread = None
            
        self.camera.release()
        
        if self.defense_service:
            self.defense_service.execute_actions([]) # Clear defenses
            
        # Save session stats
        avg_score = self.stats['sum_threat_score'] / max(1, self.stats['threat_updates'])
        self.stats['avg_threat_score'] = round(avg_score, 1)
        db.end_session(self.session_id, self.stats)
        
        if self.socketio:
            self.socketio.emit('status_update', self.get_status())
            
    def get_status(self) -> Dict[str, Any]:
        return {
            'active': self.is_running,
            'session_id': self.session_id,
            'current_threat_score': self.current_threat_score,
            'current_threat_level': self.current_threat_level,
            'screen_sensitivity': self.current_sensitivity,
            'faces_detected': len(self.last_detections)
        }
        
    def get_feed(self) -> Dict[str, Any]:
        def convert_np(obj):
            if isinstance(obj, np.integer): return int(obj)
            elif isinstance(obj, np.floating): return float(obj)
            elif isinstance(obj, np.ndarray): return obj.tolist()
            elif isinstance(obj, dict): return {k: convert_np(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)): return [convert_np(x) for x in obj]
            return obj
            
        return convert_np({
            'frame': self.camera.frame_to_base64(self.last_annotated_frame, quality=60),
            'detections': self.last_detections,
            'threat_score': self.current_threat_score,
            'threat_level': self.current_threat_level
        })

    def _draw_annotations(self, frame: np.ndarray, tracks: list):
        """Draw bounding boxes and labels on the frame for the UI."""
        annotated = frame.copy()
        
        colors = {
            'owner': (0, 255, 0),     # Green
            'trusted': (255, 165, 0), # Orange/Blue-ish
            'unknown': (0, 0, 255),   # Red
            'crossing': (0, 255, 255) # Yellow
        }
        
        for t in tracks:
            x, y, w, h = t.bbox
            color = colors.get(t.identity_type, (255, 255, 255))
            
            # Draw box
            cv2.rectangle(annotated, (x, y), (x+w, y+h), color, 2)
            
            # Draw label
            label = f"{t.identity}"
            if t.gaze_history and t.avg_gaze_score > 0.6:
                label += " (Looking)"
                
            cv2.putText(annotated, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
        return annotated

    def _monitoring_loop(self):
        """Main monitoring background thread."""
        logger.info("Monitoring loop started")
        
        last_settings_time = 0
        target_fps = 30
        base_ocr_interval = 5.0
        ocr_interval = base_ocr_interval
        
        while self.is_running:
            try:
                frame = self.camera.read_frame()
                if frame is None:
                    self.socketio.sleep(0.01)
                    continue
                    
                self.last_frame = frame
                current_time = time.time()
                
                # Reload settings periodically (every 5 seconds) to apply user changes without restart
                if current_time - last_settings_time > 5.0:
                    settings = db.get_all_settings()
                    base_ocr_interval = float(settings.get('ocr_interval', '5.0'))
                    target_fps = int(settings.get('target_fps', '30'))
                    last_settings_time = current_time
                
                # 1. OCR + NLP Analysis (Periodic)
                if current_time - self.last_ocr_time > ocr_interval and self.screen_capture and self.text_extractor and self.sensitivity_classifier:
                    try:
                        screen_img = self.screen_capture.capture_screen()
                        if screen_img is not None and self.screen_capture.has_screen_changed(screen_img):
                            # Extract text
                            extracted = self.text_extractor.extract(screen_img)
                            window_title = self.screen_capture.get_active_window_title()
                            self.current_window_title = window_title
                            # Classify
                            nlp_res = self.sensitivity_classifier.classify(extracted.full_text, window_title)
                            self.current_sensitivity = nlp_res.category
                            logger.info(f"Screen sensitivity updated: {self.current_sensitivity} (App: {window_title})")
                    except Exception as nlp_e:
                        logger.error(f"NLP/OCR Pipeline Error: {nlp_e}")
                        self.current_sensitivity = 'safe'
                    finally:
                        self.last_ocr_time = current_time
                    
                # 2. YOLO Human Filter & Phone Detection
                persons = []
                phones = []
                if self.yolo_detector:
                    persons, phones = self.yolo_detector.detect(frame)
                
                # 3. Motion/Crossing Detection
                motion_blobs = []
                is_crossing = False
                if self.motion_detector:
                    motion_blobs = self.motion_detector.detect_motion(frame)
                    is_crossing = self.motion_detector.is_crossing(frame.shape[1], current_time)
                
                # 4. Face Detection (Run on whole frame for speed)
                faces = []
                if self.face_detector and len(persons) > 0:
                    faces = self.face_detector.detect(frame)
                
                # 5. Identify, Estimate Gaze, and Associate Phones
                frame_detections = []
                for person in persons:
                    px, py, pw, ph = person['bbox']
                    
                    # Determine if holding phone (phone center or intersection is within/near person)
                    holding_phone = False
                    for phone in phones:
                        hx, hy, hw, hh = phone['bbox']
                        # Expanded bounding box intersection to catch phones slightly outside
                        if max(px-20, hx) < min(px+pw+20, hx+hw) and max(py-20, hy) < min(py+ph+20, hy+hh):
                            # Practical geometry: Is phone held up high (near face/chest) vs down low (pocket/waist)?
                            # If phone's center Y is in the upper 60% of the person's bounding box, they are holding it up to shoot.
                            p_center_y = hy + hh/2
                            if p_center_y < py + ph * 0.6:
                                holding_phone = True
                                break
                            
                    # Find a face that belongs to this person
                    best_face = None
                    for face in faces:
                        fx, fy, fw, fh = face.bbox
                        # Face center
                        f_cx, f_cy = fx + fw/2, fy + fh/2
                        if px - 20 <= f_cx <= px + pw + 20 and py - 20 <= f_cy <= py + ph + 20:
                            best_face = face
                            break
                            
                    identity = "Unknown"
                    id_type = "unknown"
                    confidence = 0.0
                    g_score = 0.0
                    
                    if best_face:
                        if self.face_recognizer:
                            identity, id_type, confidence = self.face_recognizer.identify(frame, best_face.bbox)
                        
                        if self.gaze_estimator:
                            gaze_res = self.gaze_estimator.estimate(frame, best_face.bbox)
                            if gaze_res:
                                g_score = gaze_res.gaze_score
                                if gaze_res.landmarks:
                                    import mediapipe as mp
                                    mp_face_mesh = mp.solutions.face_mesh
                                    connections_to_draw = [
                                        mp_face_mesh.FACEMESH_LIPS, mp_face_mesh.FACEMESH_LEFT_EYE,
                                        mp_face_mesh.FACEMESH_LEFT_EYEBROW, mp_face_mesh.FACEMESH_RIGHT_EYE,
                                        mp_face_mesh.FACEMESH_RIGHT_EYEBROW, mp_face_mesh.FACEMESH_FACE_OVAL
                                    ]
                                    for connection_set in connections_to_draw:
                                        for source_idx, target_idx in connection_set:
                                            if source_idx < len(gaze_res.landmarks) and target_idx < len(gaze_res.landmarks):
                                                pt1 = gaze_res.landmarks[source_idx]
                                                pt2 = gaze_res.landmarks[target_idx]
                                                cv2.line(frame, pt1, pt2, (0, 255, 0), 1)
                                                
                    # Override type if it's a fast crossing event
                    if is_crossing and id_type == 'unknown':
                        id_type = 'crossing'
                        self.stats['crossing_count'] += 1
                        
                    frame_detections.append({
                        'bbox': person['bbox'], # Track full human body, not just face!
                        'identity': identity,
                        'type': id_type,
                        'confidence': confidence,
                        'gaze_score': g_score,
                        'holding_phone': holding_phone
                    })
                    
                # Enforce Single Owner Rule
                owner_detections = [d for d in frame_detections if d['type'] == 'owner']
                if len(owner_detections) > 1:
                    owner_detections.sort(key=lambda x: x['confidence'], reverse=True)
                    for d in owner_detections[1:]:
                        d['identity'] = 'Unknown'
                        d['type'] = 'unknown'
                    
                # 6. Track Persons
                active_tracks = []
                if self.person_tracker:
                    active_tracks = self.person_tracker.update(frame_detections, current_time)
                
                # Update stats
                self.stats['total_detections'] += len(frame_detections)
                
                # Format for UI
                self.last_detections = []
                observer_data_list = []
                
                for t in active_tracks:
                    self.last_detections.append({
                        'id': t.track_id,
                        'identity': t.identity,
                        'type': t.identity_type,
                        'bbox': t.bbox,
                        'gaze_score': t.avg_gaze_score,
                        'persistence': t.persistence_seconds,
                        'holding_phone': getattr(t, 'holding_phone', False)
                    })
                    
                    behavior_score = self.behavior_analyzer.analyze(t)
                    
                    observer_data_list.append(ObserverData(
                        identity=t.identity,
                        identity_type=t.identity_type,
                        gaze_score=t.avg_gaze_score,
                        persistence_seconds=t.persistence_seconds,
                        behavior_score=behavior_score,
                        holding_phone=getattr(t, 'holding_phone', False)
                    ))
                    
                # Annotate frame
                self.last_annotated_frame = self._draw_annotations(frame, active_tracks)
                
                # 6. Calculate Threat
                threat = self.threat_calculator.calculate(observer_data_list, self.current_sensitivity, self.current_window_title)
                
                # Smoothing threat score (prevent flickering)
                self.current_threat_score = self.current_threat_score * 0.7 + threat.score * 0.3
                
                # Determine current level based on smoothed score
                if self.current_threat_score >= Config.THREAT_LEVEL_THRESHOLDS['CRITICAL']:
                    new_level = 'CRITICAL'
                elif self.current_threat_score >= Config.THREAT_LEVEL_THRESHOLDS['HIGH']:
                    new_level = 'HIGH'
                elif self.current_threat_score >= Config.THREAT_LEVEL_THRESHOLDS['MEDIUM']:
                    new_level = 'MEDIUM'
                else:
                    new_level = 'LOW'
                    
                # Threat Hysteresis (Smoothing)
                # Maintain elevated threat state for 3 seconds to prevent UI/blur flickering
                if new_level != 'LOW':
                    self.last_elevated_threat_time = current_time
                    self.elevated_threat_level = new_level
                else:
                    if current_time - getattr(self, 'last_elevated_threat_time', 0.0) < 3.0:
                        new_level = getattr(self, 'elevated_threat_level', 'LOW')
                        threat.level = new_level
                    
                level_changed = new_level != self.current_threat_level
                self.current_threat_level = new_level
                
                self.stats['sum_threat_score'] += self.current_threat_score
                self.stats['threat_updates'] += 1
                
                # 7. Defense Decisions & Actions
                if threat.level != 'LOW' or level_changed:
                    actions = self.decision_engine.decide(threat, self.current_sensitivity)
                    self.defense_service.execute_actions(actions, threat.level)
                    
                    # Log significant events
                    if threat.level in ['HIGH', 'CRITICAL']:
                        self.stats['high_risk_count'] += 1
                        
                        # Find highest threat observer
                        highest_obs = max(observer_data_list, key=lambda x: x.gaze_score * x.persistence_seconds, default=None)
                        
                        event_data = {
                            'observer_type': highest_obs.identity_type if highest_obs else 'unknown',
                            'observer_name': highest_obs.identity if highest_obs else 'Unknown',
                            'gaze_score': highest_obs.gaze_score if highest_obs else 0.0,
                            'persistence_seconds': highest_obs.persistence_seconds if highest_obs else 0.0,
                            'screen_sensitivity': self.current_sensitivity,
                            'threat_score': round(self.current_threat_score, 1),
                            'threat_level': threat.level,
                            'action_taken': ",".join([a.action_type for a in actions]),
                            'reason': threat.reason
                        }
                        db.log_event(self.session_id, event_data)
                        
                # 8. Emit Frame
                if self.socketio:
                    self.socketio.emit('frame_update', self.get_feed())
                    
                # Adaptive Resource Management
                if len(active_tracks) == 0:
                    # No one is detected: conserve resources (10 FPS, slower OCR)
                    adaptive_sleep = 0.1
                    ocr_interval = base_ocr_interval * 2.0
                else:
                    # Observers present: ramp up compute (target FPS, normal OCR)
                    adaptive_sleep = 1.0 / max(target_fps, 5)
                    ocr_interval = base_ocr_interval
                    
                self.socketio.sleep(adaptive_sleep)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                logger.error(traceback.format_exc())
                self.socketio.sleep(1.0) # Back off on error
                
        logger.info("Monitoring loop terminated")
