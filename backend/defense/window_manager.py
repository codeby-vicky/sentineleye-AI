import ctypes
from utils.logger import logger

class WindowManager:
    def __init__(self):
        pass
        
    def minimize_active_window(self):
        """Minimize the currently active foreground window (Windows only)."""
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                user32.ShowWindow(hwnd, 6) # SW_MINIMIZE = 6
                logger.info("Minimized active window")
        except Exception as e:
            logger.error(f"Failed to minimize active window: {e}")
            
    def minimize_all_windows(self):
        """Minimize all open windows."""
        try:
            import pyautogui
            pyautogui.hotkey('win', 'd')
            logger.info("Minimized all windows via Win+D")
        except ImportError:
            logger.error("pyautogui not installed. Cannot minimize all windows.")
        except Exception as e:
            logger.error(f"Failed to minimize all windows: {e}")
            
    def get_active_window_bounds(self):
        """Get bounds of active window: return {x, y, w, h} or None."""
        try:
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                rect = wintypes.RECT()
                if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    return {
                        'x': rect.left,
                        'y': rect.top,
                        'w': rect.right - rect.left,
                        'h': rect.bottom - rect.top
                    }
        except Exception as e:
            logger.error(f"Failed to get window bounds: {e}")
        return None
