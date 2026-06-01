from flask import Blueprint, request, jsonify
from database.db import db

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

@settings_bp.route('/apps/running', methods=['GET'])
def get_running_apps():
    from utils.windows_apps import list_running_apps
    apps = list_running_apps()
    return jsonify({'apps': apps})
