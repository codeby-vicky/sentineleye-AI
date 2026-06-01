from flask import Blueprint, request, jsonify, Response
from database.db import db
import csv
import io

logs_bp = Blueprint('logs', __name__, url_prefix='/api/events')

@logs_bp.route('', methods=['GET'])
def get_events():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    filters = {
        'observer_type': request.args.get('observer_type'),
        'threat_level': request.args.get('threat_level')
    }
    
    offset = (page - 1) * per_page
    
    events, total = db.get_events(limit=per_page, offset=offset, filters=filters)
    
    return jsonify({
        'events': events,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })

@logs_bp.route('/export', methods=['GET'])
def export_events():
    events, _ = db.get_events(limit=10000, offset=0)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if events:
        # Write headers
        writer.writerow(events[0].keys())
        # Write data
        for event in events:
            writer.writerow(event.values())
            
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=sentineleye_events.csv"}
    )
