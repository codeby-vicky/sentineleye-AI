from flask import Blueprint, request, jsonify
import cv2
import numpy as np
from services.auth_service import AuthService
from ai.face_recognizer import FaceRecognizer

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def get_auth_service():
    from ai.face_recognizer import FaceRecognizer
    from services.auth_service import AuthService
    return AuthService(FaceRecognizer())

@auth_bp.route('/register-owner', methods=['POST'])
def register_owner():
    name = request.form.get('name')
    if not name:
        return jsonify({'success': False, 'message': 'Name is required'}), 400
        
    images = request.files.getlist('images')
    if not images or len(images) == 0:
        return jsonify({'success': False, 'message': 'Face images are required'}), 400
        
    frames = []
    for file in images:
        npimg = np.fromfile(file, np.uint8)
        frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        if frame is not None:
            frames.append(frame)
            
    if not frames:
        return jsonify({'success': False, 'message': 'Invalid images provided'}), 400
        
    success = get_auth_service().register_owner(name, frames)
    
    if success:
        return jsonify({'success': True, 'message': 'Owner registered successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to extract face embeddings. Ensure face is clearly visible.'}), 400

# Store temporary captures in memory (keyed by name)
registration_cache = {}

@auth_bp.route('/capture-angle', methods=['POST'])
def capture_angle():
    data = request.json or {}
    name = data.get('name')
    angle = data.get('angle')
    
    if not name or not angle:
        return jsonify({'success': False, 'message': 'Name and angle required'}), 400
        
    from ai.camera_manager import CameraManager
    from ai.face_detector import FaceDetector
    import time
    cam = CameraManager()
    
    try:
        face_detector = FaceDetector()
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to initialize models: {str(e)}'}), 500
    
    frames = []
    issues = set()
    # Capture up to 3 good quality frames for this angle
    for _ in range(15):
        frame = cam.read_frame()
        if frame is not None:
            # 1. Check Brightness (too dark or overexposed)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            if brightness < 40:
                issues.add("Too dark")
                continue
            if brightness > 240:
                issues.add("Too bright/overexposed")
                continue
                
            # 2. Check Motion Blur (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 100:  # Threshold for blurriness
                issues.add("Face blurred or moving too fast")
                continue
                
            faces = face_detector.detect(frame)
            if faces:
                best_face = max(faces, key=lambda f: f.bbox[2] * f.bbox[3])
                # 3. Check Confidence and Size
                if best_face.confidence < 0.6:
                    issues.add("Face not clear enough (low confidence)")
                    continue
                if best_face.bbox[2] < 50 or best_face.bbox[3] < 50:
                    issues.add("Face too far/small")
                    continue
                    
                frames.append(frame)
                if len(frames) == 3:
                    break
        time.sleep(0.1)
        
    if len(frames) < 3:
        error_msg = f'Could not capture {angle} angle clearly.'
        if issues:
            error_msg += ' Issues: ' + ', '.join(issues)
        return jsonify({'success': False, 'message': error_msg}), 400
        
    if name not in registration_cache:
        registration_cache[name] = []
        
    registration_cache[name].append({
        'angle': angle,
        'frames': frames
    })
    
    return jsonify({'success': True, 'message': f'Angle {angle} captured'})

@auth_bp.route('/finalize-registration', methods=['POST'])
def finalize_registration():
    data = request.json or {}
    name = data.get('name')
    
    if not name or name not in registration_cache:
        return jsonify({'success': False, 'message': 'No captures found for this user'}), 400
        
    captures = registration_cache[name]
    if len(captures) < 5:
        return jsonify({'success': False, 'message': 'Incomplete angles captured'}), 400
        
    # Flatten all frames
    all_frames = []
    angle_metadata = []
    
    for cap in captures:
        for f in cap['frames']:
            all_frames.append(f)
            angle_metadata.append(cap['angle'])
            
    # Modify auth_service to accept frames and metadata
    success = get_auth_service().register_owner(name, all_frames, angle_metadata)
    
    # Cleanup
    del registration_cache[name]
    
    if success:
        return jsonify({'success': True, 'message': 'Owner registered successfully with multi-angle data'})
    else:
        return jsonify({'success': False, 'message': 'Failed to extract face embeddings.'}), 400

@auth_bp.route('/verify-owner', methods=['POST'])
def verify_owner():
    import base64
    
    data = request.json
    if not data or 'image' not in data:
        return jsonify({'success': False, 'message': 'Image required'}), 400
        
    img_data = data['image']
    if 'base64,' in img_data:
        img_data = img_data.split('base64,')[1]
        
    try:
        nparr = np.frombuffer(base64.b64decode(img_data), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        is_owner = get_auth_service().verify_owner(frame)
        
        if is_owner:
            owner = get_auth_service().get_owner()
            return jsonify({
                'verified': True,
                'name': owner['name'] if owner else 'Owner'
            })
        else:
            return jsonify({
                'verified': False,
                'message': 'Face does not match owner'
            }), 401
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@auth_bp.route('/owner', methods=['GET'])
def get_owner_route():
    owner = get_auth_service().get_owner()
    if owner:
        return jsonify(owner)
    return jsonify({'message': 'No owner registered'}), 404
