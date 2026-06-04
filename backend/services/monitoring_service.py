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
        self.object_detector = None
        
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
        
        # Frame scheduling caches
        self._frame_count = 0
        self._cached_obj_results = {'persons': [], 'phones': [], 'raw_phone_bboxes': []}
        self._cached_identities = {}  # bbox_key -> (identity, type, confidence)
        self._cached_gaze_results = {}  # bbox_key -> GazeResult
        
        # Owner tracking for relative positioning
        self._owner_face_area = 0
        self._owner_person_bbox = None
        
        # Defense state tracking — prevents spam
        self._last_defense_level = 'LOW'
        self._last_event_log_time = 0
        self._event_log_cooldown = 10.0  # Seconds between event logs
        
        # MediaPipe imports cached
        self._mp_face_mesh = None
        self._mp_connections = None
        
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
                from ai.object_detector import ObjectDetector
                self.face_detector = FaceDetector()
                self.face_recognizer = FaceRecognizer()
                self.gaze_estimator = GazeEstimator()
                self.person_tracker = PersonTracker()
                self.object_detector = ObjectDetector()
            except Exception as e:
                logger.error(f"Error loading core CV modules: {e}")
                logger.error(traceback.format_exc())
                
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
            
            # Cache MediaPipe imports for annotation
            try:
                import mediapipe as mp
                self._mp_face_mesh = mp.solutions.face_mesh
                self._mp_connections = [
                    self._mp_face_mesh.FACEMESH_LIPS,
                    self._mp_face_mesh.FACEMESH_LEFT_EYE,
                    self._mp_face_mesh.FACEMESH_LEFT_EYEBROW,
                    self._mp_face_mesh.FACEMESH_RIGHT_EYE,
                    self._mp_face_mesh.FACEMESH_RIGHT_EYEBROW,
                    self._mp_face_mesh.FACEMESH_FACE_OVAL
                ]
            except Exception as e:
                logger.warning(f"Could not cache MediaPipe imports: {e}")
            
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
        
        # Reset caches
        self._frame_count = 0
        self._cached_obj_results = {'persons': [], 'phones': [], 'raw_phone_bboxes': []}
        self._cached_identities = {}
        self._cached_gaze_results = {}
        self._owner_face_area = 0
        self._owner_person_bbox = None
        self._last_defense_level = 'LOW'
        self._last_event_log_time = 0
        self.current_threat_score = 0.0
        self.current_threat_level = 'LOW'
            
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
            self.defense_service.execute_actions([], 'LOW')  # Clear defenses
            self.defense_service.alert_manager.clear_state()
            self.defense_service.screen_blur.reset()
            
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
        return {
            'frame': self.camera.frame_to_base64(self.last_annotated_frame, quality=60),
            'detections': self.last_detections,
            'threat_score': self.current_threat_score,
            'threat_level': self.current_threat_level
        }

    def _draw_annotations(self, frame: np.ndarray, tracks: list):
        """Draw bounding boxes and labels on the frame for the UI."""
        annotated = frame.copy()
        
        colors = {
            'owner': (0, 255, 0),     # Green
            'trusted': (255, 165, 0), # Orange
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

    def _bbox_key(self, bbox):
        """Create a hashable key from a bbox for caching."""
        x, y, w, h = bbox
        # Quantize to reduce cache misses from tiny movements
        return (x // 10, y // 10, w // 10, h // 10)

    def _determine_relative_position(self, owner_bbox, unknown_bbox, frame_width):
        """
        Determine the position of an unknown person relative to the owner.
        Returns: 'behind', 'beside', 'front', 'unknown'
        """
        if owner_bbox is None or unknown_bbox is None:
            return 'unknown'
            
        ox, oy, ow, oh = owner_bbox
        ux, uy, uw, uh = unknown_bbox
        
        owner_area = ow * oh
        unknown_area = uw * uh
        
        # If unknown face is significantly smaller, they're likely farther/behind
        area_ratio = unknown_area / max(owner_area, 1)
        
        # Center positions
        owner_cx = ox + ow // 2
        unknown_cx = ux + uw // 2
        
        # Horizontal overlap check
        horizontal_overlap = abs(owner_cx - unknown_cx) < (ow + uw) // 2
        
        if area_ratio < 0.6 and horizontal_overlap:
            return 'behind'  # Smaller face, same horizontal position = behind
        elif area_ratio < 0.6:
            return 'beside'  # Smaller face, different position = beside/farther
        elif area_ratio > 1.2:
            return 'front'   # Larger face = closer/in front
        else:
            return 'beside'

    def _monitoring_loop(self):
        """Main monitoring background thread with hybrid CPU+GPU scheduling."""
        logger.info("Monitoring loop started")
        
        settings = db.get_all_settings()
        ocr_interval = float(settings.get('ocr_interval', '5.0'))
        
        # Consecutive error tracking
        consecutive_errors = 0
        
        while self.is_running:
            try:
                frame = self.camera.read_frame()
                if frame is None:
                    self.socketio.sleep(0.01)
                    consecutive_errors += 1
                    if consecutive_errors > 90:  # ~3 seconds of no frames
                        logger.warning("Too many consecutive frame failures, attempting camera restart")
                        camera_index = int(db.get_all_settings().get('camera_index', '0'))
                        self.camera.release()
                        self.camera.open(camera_index, Config.CAMERA_RESOLUTION)
                        consecutive_errors = 0
                    continue
                
                consecutive_errors = 0
                self.last_frame = frame
                current_time = time.time()
                self._frame_count += 1
                
                # ================================================================
                # STAGE 1: OCR + NLP (CPU, periodic — every ~5 seconds)
                # ================================================================
                if current_time - self.last_ocr_time > ocr_interval and self.screen_capture and self.text_extractor and self.sensitivity_classifier:
                    try:
                        screen_img = self.screen_capture.capture_screen()
                        if screen_img is not None and self.screen_capture.has_screen_changed(screen_img):
                            extracted = self.text_extractor.extract(screen_img)
                            window_title = self.screen_capture.get_active_window_title()
                            self.current_window_title = window_title
                            nlp_res = self.sensitivity_classifier.classify(extracted.full_text, window_title)
                            self.current_sensitivity = nlp_res.category
                            logger.info(f"Screen sensitivity: {self.current_sensitivity} (App: {window_title})")
                    except Exception as nlp_e:
                        logger.error(f"NLP/OCR Pipeline Error: {nlp_e}")
                        self.current_sensitivity = 'safe'
                    finally:
                        self.last_ocr_time = current_time
                    
                # ================================================================
                # STAGE 2: YOLO Object Detection (GPU, every 3rd frame)
                # ================================================================
                if self.object_detector and self._frame_count % Config.SCHEDULE_YOLO == 0:
                    self._cached_obj_results = self.object_detector.detect(frame)
                
                obj_results = self._cached_obj_results
                    
                # ================================================================
                # STAGE 3: Face Detection (CPU/MediaPipe, every frame)
                # ================================================================
                faces = []
                if self.face_detector:
                    all_faces = self.face_detector.detect(frame)
                    # Filter: only keep faces inside YOLO person bboxes
                    if self.object_detector and obj_results['persons']:
                        for face in all_faces:
                            if self.object_detector.is_face_in_person(face.bbox, obj_results['persons']):
                                faces.append(face)
                    else:
                        faces = all_faces
                
                # ================================================================
                # STAGE 4: Motion/Crossing Detection (CPU, every frame)
                # ================================================================
                motion_blobs = []
                is_crossing = False
                if self.motion_detector:
                    motion_blobs = self.motion_detector.detect_motion(frame)
                    is_crossing = self.motion_detector.is_crossing(frame.shape[1], current_time)
                
                # ================================================================
                # STAGE 5: Face Recognition (GPU/InsightFace, every 5th frame)
                # Uses cached results between recognition frames
                # ================================================================
                run_recognition = (self._frame_count % Config.SCHEDULE_FACE_RECOGNIZE == 0)
                
                frame_detections = []
                owner_face_bbox = None
                
                for face in faces:
                    identity = "Unknown"
                    id_type = "unknown"
                    confidence = 0.0
                    
                    bbox_key = self._bbox_key(face.bbox)
                    
                    if self.face_recognizer:
                        if run_recognition:
                            # Run actual recognition
                            identity, id_type, confidence = self.face_recognizer.identify(frame, face.bbox)
                            self._cached_identities[bbox_key] = (identity, id_type, confidence)
                        else:
                            # Use cached result if available for similar bbox
                            cached = self._cached_identities.get(bbox_key)
                            if cached:
                                identity, id_type, confidence = cached
                            else:
                                # No cache hit — run recognition anyway for new faces
                                identity, id_type, confidence = self.face_recognizer.identify(frame, face.bbox)
                                self._cached_identities[bbox_key] = (identity, id_type, confidence)
                    
                    # Track owner face
                    if id_type == 'owner':
                        owner_face_bbox = face.bbox
                        self._owner_face_area = face.bbox[2] * face.bbox[3]
                    
                    # Override type for fast crossing
                    if is_crossing and id_type == 'unknown':
                        id_type = 'crossing'
                        self.stats['crossing_count'] += 1
                        
                    # ================================================================
                    # STAGE 5b: Gaze Estimation (CPU/MediaPipe, every frame)
                    # ================================================================
                    g_score = 0.0
                    if self.gaze_estimator:
                        gaze_res = self.gaze_estimator.estimate(frame, face.bbox)
                        if gaze_res:
                            g_score = gaze_res.gaze_score
                            # Draw mesh landmarks using cached imports
                            if gaze_res.landmarks and self._mp_connections:
                                for connection_set in self._mp_connections:
                                    for source_idx, target_idx in connection_set:
                                        if source_idx < len(gaze_res.landmarks) and target_idx < len(gaze_res.landmarks):
                                            pt1 = gaze_res.landmarks[source_idx]
                                            pt2 = gaze_res.landmarks[target_idx]
                                            cv2.line(frame, pt1, pt2, (0, 255, 0), 1)
                            
                    frame_detections.append({
                        'bbox': face.bbox,
                        'identity': identity,
                        'type': id_type,
                        'confidence': confidence,
                        'gaze_score': g_score
                    })
                    
                # Enforce Single Owner Rule
                owner_detections = [d for d in frame_detections if d['type'] == 'owner']
                if len(owner_detections) > 1:
                    owner_detections.sort(key=lambda x: x['confidence'], reverse=True)
                    for d in owner_detections[1:]:
                        d['identity'] = 'Unknown'
                        d['type'] = 'unknown'
                    
                # ================================================================
                # STAGE 6: Person Tracking
                # ================================================================
                active_tracks = []
                if self.person_tracker:
                    active_tracks = self.person_tracker.update(frame_detections, current_time)
                
                # Find owner's person bbox from YOLO results
                self._owner_person_bbox = None
                if owner_face_bbox and obj_results['persons']:
                    ofx, ofy, ofw, ofh = owner_face_bbox
                    owner_face_cx = ofx + ofw // 2
                    owner_face_cy = ofy + ofh // 2
                    for pbbox in obj_results['persons']:
                        px, py, pw, ph = pbbox
                        if (px - 20 <= owner_face_cx <= px + pw + 20) and \
                           (py - 20 <= owner_face_cy <= py + ph + 20):
                            self._owner_person_bbox = pbbox
                            break
                
                # Update stats
                self.stats['total_detections'] += len(frame_detections)
                
                # ================================================================
                # STAGE 7: Build Observer Data with relative positioning
                # Minimum persistence filter: unknowns must exist 2+ seconds
                # ================================================================
                self.last_detections = []
                observer_data_list = []
                
                for t in active_tracks:
                    self.last_detections.append({
                        'id': t.track_id,
                        'identity': t.identity,
                        'type': t.identity_type,
                        'bbox': t.bbox,
                        'gaze_score': t.avg_gaze_score,
                        'persistence': t.persistence_seconds
                    })
                    
                    # CRITICAL: Skip unknown observers with < 2s persistence for threat scoring
                    # This prevents false "Unknown Person Standing Behind" from brief detections
                    if t.identity_type in ('unknown', 'crossing') and t.persistence_seconds < 2.0:
                        continue
                    
                    behavior_score = self.behavior_analyzer.analyze(t)
                    
                    # Calculate face area ratio relative to owner
                    face_area_ratio = 0.0
                    if self._owner_face_area > 0 and t.identity_type != 'owner':
                        face_area_ratio = t.face_area / max(self._owner_face_area, 1)
                    
                    # Determine relative position
                    relative_position = 'unknown'
                    if t.identity_type != 'owner' and owner_face_bbox:
                        relative_position = self._determine_relative_position(
                            owner_face_bbox, t.bbox, frame.shape[1]
                        )
                    
                    observer_data_list.append(ObserverData(
                        identity=t.identity,
                        identity_type=t.identity_type,
                        gaze_score=t.avg_gaze_score,
                        persistence_seconds=t.persistence_seconds,
                        behavior_score=behavior_score,
                        face_area_ratio=face_area_ratio,
                        relative_position=relative_position,
                        is_approaching=t.is_approaching
                    ))
                    
                # Annotate frame
                self.last_annotated_frame = self._draw_annotations(frame, active_tracks)
                
                # ================================================================
                # STAGE 8: Calculate Threat
                # ================================================================
                threat = self.threat_calculator.calculate(observer_data_list, self.current_sensitivity, self.current_window_title)
                
                # ================================================================
                # STAGE 9: Phone Detection Threat Escalation
                # ================================================================
                phone_detections = obj_results.get('phones', [])
                if phone_detections:
                    threat.phone_detected = True
                    max_phone_risk = 'low'
                    
                    for phone_det in phone_detections:
                        if hasattr(phone_det, 'risk_level'):
                            if phone_det.risk_level == 'high':
                                max_phone_risk = 'high'
                            elif phone_det.risk_level == 'medium' and max_phone_risk != 'high':
                                max_phone_risk = 'medium'
                    
                    # Determine who is holding each phone
                    other_person_bboxes = []
                    for pbbox in obj_results['persons']:
                        if pbbox != self._owner_person_bbox:
                            other_person_bboxes.append(pbbox)
                    
                    for phone_det in phone_detections:
                        phone_bbox = phone_det.bbox if hasattr(phone_det, 'bbox') else None
                        if phone_bbox and self.object_detector:
                            holder = self.object_detector.get_phone_owner_association(
                                phone_bbox, self._owner_person_bbox,
                                other_person_bboxes, frame.shape[1]
                            )
                            
                            if holder == 'owner':
                                # Owner's phone — no threat escalation
                                continue
                            elif holder == 'none':
                                # Phone on desk or unattended — minimal threat
                                threat.score = min(100.0, threat.score + 5.0)
                                threat.reason = "Unattended Phone Detected"
                            elif holder == 'unknown':
                                # Unknown person holding phone
                                if max_phone_risk == 'high':
                                    threat.score = min(100.0, threat.score + 50.0)
                                    threat.reason = "CRITICAL: Unknown Person Recording Screen"
                                elif max_phone_risk == 'medium':
                                    threat.score = min(100.0, threat.score + 30.0)
                                    threat.reason = "Phone Detected Near Unknown Observer"
                                else:
                                    threat.score = min(100.0, threat.score + 20.0)
                                    threat.reason = "Unknown Person Holding Phone"
                    
                    # Update phone_risk on non-owner observers
                    for obs in observer_data_list:
                        if obs.identity_type != 'owner':
                            obs.phone_risk = max_phone_risk
                
                # ================================================================
                # STAGE 10: Threat Score Smoothing
                # ================================================================
                self.current_threat_score = self.current_threat_score * 0.7 + threat.score * 0.3
                
                # Determine level from smoothed score
                if self.current_threat_score >= Config.THREAT_LEVEL_THRESHOLDS['CRITICAL']:
                    new_level = 'CRITICAL'
                elif self.current_threat_score >= Config.THREAT_LEVEL_THRESHOLDS['HIGH']:
                    new_level = 'HIGH'
                elif self.current_threat_score >= Config.THREAT_LEVEL_THRESHOLDS['MEDIUM']:
                    new_level = 'MEDIUM'
                else:
                    new_level = 'LOW'
                    
                level_changed = new_level != self.current_threat_level
                self.current_threat_level = new_level
                
                self.stats['sum_threat_score'] += self.current_threat_score
                self.stats['threat_updates'] += 1
                
                # ================================================================
                # STAGE 11: Defense Actions — STATE CHANGE ONLY
                # Only trigger defense when threat level changes
                # ================================================================
                if level_changed:
                    # Use smoothed level for defense decisions
                    from risk_engine.threat_calculator import ThreatResult
                    smoothed_threat = ThreatResult(
                        score=self.current_threat_score,
                        level=new_level,
                        reason=threat.reason,
                        contributing_factors=threat.contributing_factors,
                        phone_detected=threat.phone_detected
                    )
                    
                    if new_level == 'LOW':
                        # Transitioning to safe — clear defenses
                        self.defense_service.execute_actions([], 'LOW')
                    else:
                        actions = self.decision_engine.decide(smoothed_threat)
                        self.defense_service.execute_actions(actions, new_level)
                    
                    self._last_defense_level = new_level
                    
                    # Log event with cooldown
                    if new_level in ('HIGH', 'CRITICAL'):
                        self.stats['high_risk_count'] += 1
                        
                        if (current_time - self._last_event_log_time) >= self._event_log_cooldown:
                            self._last_event_log_time = current_time
                            highest_obs = max(observer_data_list, key=lambda x: x.gaze_score * x.persistence_seconds, default=None)
                            
                            event_data = {
                                'observer_type': highest_obs.identity_type if highest_obs else 'unknown',
                                'observer_name': highest_obs.identity if highest_obs else 'Unknown',
                                'gaze_score': highest_obs.gaze_score if highest_obs else 0.0,
                                'persistence_seconds': highest_obs.persistence_seconds if highest_obs else 0.0,
                                'screen_sensitivity': self.current_sensitivity,
                                'threat_score': round(self.current_threat_score, 1),
                                'threat_level': new_level,
                                'action_taken': ",".join([a.action_type for a in actions]),
                                'reason': threat.reason
                            }
                            db.log_event(self.session_id, event_data)
                        
                # ================================================================
                # STAGE 12: Emit Frame
                # ================================================================
                if self.socketio:
                    self.socketio.emit('frame_update', self.get_feed())
                    
                # Throttle to ~30 FPS
                self.socketio.sleep(0.03)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                logger.error(traceback.format_exc())
                consecutive_errors += 1
                self.socketio.sleep(1.0)
                
        logger.info("Monitoring loop terminated")
