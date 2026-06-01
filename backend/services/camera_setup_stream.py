import threading
import time
from ai.camera_manager import CameraManager
from utils.logger import logger

class CameraSetupStream:
    def __init__(self, socketio):
        self.socketio = socketio
        self.camera = CameraManager()
        self.is_streaming = False
        self.thread = None

    def start(self, camera_index=0):
        if self.is_streaming: 
            return True
            
        logger.info(f"Starting Setup Camera Stream on index {camera_index}...")
        
        # Try multiple fallback indices if the requested one fails
        indices_to_try = [camera_index] + [i for i in range(3) if i != camera_index]
        opened = False
        
        for idx in indices_to_try:
            if self.camera.open(idx):
                opened = True
                break
                
        if not opened:
            logger.error("Failed to open any camera for setup stream")
            return False
            
        self.is_streaming = True
        self.thread = self.socketio.start_background_task(self._stream_loop)
        return True

    def stop(self):
        logger.info("Stopping Setup Camera Stream...")
        self.is_streaming = False
        self.thread = None
        self.camera.release()

    def _stream_loop(self):
        failed_frames = 0
        current_idx = 0
        
        # Lazy load AI for mesh visualization
        try:
            from ai.face_detector import FaceDetector
            from ai.gaze_estimator import GazeEstimator
            import cv2
            face_detector = FaceDetector()
            gaze_estimator = GazeEstimator()
        except Exception as e:
            logger.error(f"Failed to load AI modules for setup stream: {e}")
            face_detector = None
            gaze_estimator = None
        
        while self.is_streaming:
            try:
                frame = self.camera.read_frame()
                if frame is not None:
                    failed_frames = 0
                    
                    # Draw clean green face contours
                    if face_detector and gaze_estimator:
                        faces = face_detector.detect(frame)
                        if faces:
                            # Largest face
                            largest_face = max(faces, key=lambda f: f.bbox[2] * f.bbox[3])
                            gaze_res = gaze_estimator.estimate(frame, largest_face.bbox)
                            if gaze_res and gaze_res.landmarks:
                                import mediapipe as mp
                                mp_face_mesh = mp.solutions.face_mesh
                                
                                # Draw specific clean contours
                                connections_to_draw = [
                                    mp_face_mesh.FACEMESH_LIPS,
                                    mp_face_mesh.FACEMESH_LEFT_EYE,
                                    mp_face_mesh.FACEMESH_LEFT_EYEBROW,
                                    mp_face_mesh.FACEMESH_RIGHT_EYE,
                                    mp_face_mesh.FACEMESH_RIGHT_EYEBROW,
                                    mp_face_mesh.FACEMESH_FACE_OVAL
                                ]
                                
                                for connection_set in connections_to_draw:
                                    for source_idx, target_idx in connection_set:
                                        if source_idx < len(gaze_res.landmarks) and target_idx < len(gaze_res.landmarks):
                                            pt1 = gaze_res.landmarks[source_idx]
                                            pt2 = gaze_res.landmarks[target_idx]
                                            cv2.line(frame, pt1, pt2, (0, 255, 0), 1)
                    
                    b64 = self.camera.frame_to_base64(frame, quality=60)
                    if self.socketio:
                        self.socketio.emit('setup_frame_update', {'frame': b64})
                else:
                    failed_frames += 1
                    # If we fail for ~2 seconds (60 frames), try next camera
                    if failed_frames > 60:
                        logger.warning("Camera yielding empty frames. Trying next index...")
                        current_idx = (current_idx + 1) % 3
                        self.camera.open(current_idx)
                        failed_frames = 0
                        # Emit a warning to UI
                        if self.socketio:
                            self.socketio.emit('setup_frame_update', {'error': 'Camera unavailable, trying next device...'})
            except Exception as e:
                logger.error(f"Error in setup stream loop: {e}")
            
            # ~30 fps
            self.socketio.sleep(0.033)
