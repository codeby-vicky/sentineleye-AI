import ctypes
from ctypes import wintypes
from utils.logger import logger

def list_running_apps():
    """
    Returns a list of titles for all visible, non-empty, top-level windows.
    Useful for populating the Privacy Applications selector.
    """
    try:
        user32 = ctypes.windll.user32
        windows = []
        
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        
        def enum_windows_proc(hwnd, lParam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value
                    if title and title.strip():
                        windows.append(title.strip())
            return True

        user32.EnumWindows(WNDENUMPROC(enum_windows_proc), 0)
        
        # Deduplicate and sort
        unique_windows = sorted(list(set(windows)))
        return unique_windows
    except Exception as e:
        logger.error(f"Failed to list running apps: {e}")
        return []
