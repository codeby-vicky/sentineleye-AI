import ctypes
from utils.logger import logger

def lock_workstation():
    """Lock the Windows workstation immediately."""
    try:
        logger.warning("LOCKING WORKSTATION")
        ctypes.windll.user32.LockWorkStation()
    except Exception as e:
        logger.error(f"Failed to lock workstation: {e}")
