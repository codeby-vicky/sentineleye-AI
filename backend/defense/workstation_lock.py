import ctypes
from utils.logger import logger

def sleep_display():
    """Turn off the display (sleep monitor) without locking the workstation.
    The owner can wake the display by moving the mouse."""
    try:
        logger.warning("SLEEPING DISPLAY — privacy protection")
        # WM_SYSCOMMAND with SC_MONITORPOWER, 2 = turn off monitor
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
    except Exception as e:
        logger.error(f"Failed to sleep display: {e}")

# Keep backward-compatible alias
def lock_workstation():
    """Legacy alias — now sleeps display instead of locking."""
    sleep_display()
