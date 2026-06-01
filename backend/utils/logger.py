import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from config import Config

def setup_logger(name):
    """Setup and return a logger with standard formatting."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        Config.init_app()
        log_file = os.path.join(Config.LOGS_DIR, 'sentineleye.log')
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

# Global logger
logger = setup_logger('SentinelEye')
