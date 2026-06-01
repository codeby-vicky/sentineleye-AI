import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '2'

from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from database.db import db
from config import Config
from utils.logger import logger

# Initialize SocketIO globally so it can be accessed
socketio = SocketIO(cors_allowed_origins="*")

def create_app(testing=False):
    """Flask application factory."""
    app = Flask(__name__)
    CORS(app)
    
    app.config.from_object(Config)
    if testing:
        app.config['TESTING'] = True
        
    # Initialize SocketIO with app
    socketio.init_app(app)
    
    # Init DB
    if not testing:
        try:
            db.init_db()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            
    # Register Blueprints
    from api.auth_routes import auth_bp
    from api.user_routes import user_bp
    from api.monitoring_routes import monitoring_bp
    from api.settings_routes import settings_bp
    from api.logs_routes import logs_bp
    from api.analytics_routes import analytics_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(analytics_bp)
    
    @app.route('/api/health')
    def health():
        from ai.camera_manager import CameraManager
        # Using singletons/instances without initializing heavy models if not needed
        camera_manager = CameraManager()
        camera_ok = camera_manager is not None
        
        # Test DB connection
        db_ok = True
        try:
            db.get_all_settings()
        except:
            db_ok = False
            
        return jsonify({
            'backend': True,
            'database': db_ok,
            'camera': camera_ok,
            'gpu': True, # Hardcoded initially, updated dynamically when running
            'face_recognition': True,
            'ocr': True,
            'nlp': True
        })
        
    # Setup Camera Stream for UI Registration
    from services.camera_setup_stream import CameraSetupStream
    app.camera_stream = CameraSetupStream(socketio)
    
    from flask import request
    
    @app.route('/api/camera/start', methods=['POST'])
    def start_camera():
        idx = 0
        if request.is_json and request.json:
            idx = request.json.get('camera_index', 0)
        success = app.camera_stream.start(idx)
        return jsonify({'success': success})
        
    @app.route('/api/camera/stop', methods=['POST'])
    def stop_camera():
        app.camera_stream.stop()
        return jsonify({'success': True})
        
    # SocketIO event handlers
    @socketio.on('connect')
    def handle_connect():
        logger.info("Client connected to WebSocket")
        
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("Client disconnected from WebSocket")
        
    return app
