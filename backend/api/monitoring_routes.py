from flask import Blueprint, jsonify
from services.monitoring_service import MonitoringService

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')

@monitoring_bp.route('/start', methods=['POST'])
def start_monitoring():
    from app import socketio
    service = MonitoringService(socketio)
    session_id = service.start_session()
    
    if session_id != -1:
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Monitoring started'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to start camera or monitoring'
        }), 500

@monitoring_bp.route('/stop', methods=['POST'])
def stop_monitoring():
    from app import socketio
    service = MonitoringService(socketio)
    if not service.is_running:
        return jsonify({'success': True, 'message': 'Already stopped'})
        
    service.stop_session()
    
    return jsonify({
        'success': True,
        'message': 'Monitoring stopped',
        'session_summary': service.stats
    })

@monitoring_bp.route('/status', methods=['GET'])
def get_status():
    from app import socketio
    service = MonitoringService(socketio)
    return jsonify(service.get_status())

@monitoring_bp.route('/feed', methods=['GET'])
def get_feed():
    from app import socketio
    service = MonitoringService(socketio)
    if not service.is_running:
        return jsonify({'error': 'Monitoring is not running'}), 400
        
    return jsonify(service.get_feed())
