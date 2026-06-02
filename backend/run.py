import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, socketio
from utils.logger import logger
from utils.gpu_utils import get_gpu_info

def main():
    logger.info("Starting SentinelEye AI Backend...")
    
    # Check GPU capabilities
    get_gpu_info()
    
    # Create app
    app = create_app()
    
    # Run server
    port = 5000
    logger.info(f"Flask server starting on port {port}")
    
    # Use SocketIO's run which uses eventlet/gevent under the hood
    socketio.run(app, host='127.0.0.1', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
