from flask import Blueprint, request, jsonify
from database.db import db
from config import Config

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

@settings_bp.route('', methods=['GET'])
def get_settings():
    settings = db.get_all_settings()
    return jsonify({'settings': settings})

@settings_bp.route('', methods=['PUT'])
def update_settings():
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
        
    for key, value in data.items():
        db.update_setting(key, str(value))
        
    return jsonify({'success': True, 'message': 'Settings updated'})

@settings_bp.route('/profile/<profile_name>', methods=['POST'])
def apply_profile(profile_name):
    """Apply a performance profile (low, balanced, high)."""
    profiles = Config.PERFORMANCE_PROFILES
    if profile_name not in profiles:
        return jsonify({'success': False, 'message': f'Unknown profile: {profile_name}'}), 400
    
    profile = profiles[profile_name]
    # Save profile name to settings
    db.update_setting('performance_profile', profile_name)
    db.update_setting('ocr_interval', str(profile['ocr_interval']))
    
    return jsonify({'success': True, 'profile': profile_name, 'settings': profile})

@settings_bp.route('/apps/running', methods=['GET'])
def get_running_apps():
    from utils.windows_apps import list_running_apps
    apps = list_running_apps()
    return jsonify({'apps': apps})
