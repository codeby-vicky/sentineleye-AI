import numpy as np
from datetime import datetime, timezone

def numpy_to_bytes(arr: np.ndarray) -> bytes:
    """Serialize a numpy array to bytes for database storage."""
    return arr.tobytes()

def bytes_to_numpy(data: bytes, shape=(128,), dtype=np.float64) -> np.ndarray:
    """Deserialize bytes from database to a numpy array."""
    if not data:
        return np.array([])
    return np.frombuffer(data, dtype=dtype).reshape(shape)

def generate_timestamp() -> str:
    """Generate ISO-8601 formatted UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()

def format_duration(seconds: float) -> str:
    """Format duration in seconds to HH:MM:SS string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
