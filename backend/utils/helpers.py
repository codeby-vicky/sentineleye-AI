import numpy as np
from datetime import datetime, timezone

def numpy_to_bytes(arr: np.ndarray) -> bytes:
    """Serialize a numpy array to bytes for database storage."""
    return arr.tobytes()

def bytes_to_numpy(data: bytes, dtype=np.float64) -> np.ndarray:
    """Deserialize bytes from database to a numpy array, auto-detecting shape."""
    if not data:
        return np.array([])
    
    # Each float64 takes 8 bytes.
    # An embedding is 128 elements.
    elements = len(data) // 8
    
    if elements == 0:
        return np.array([])
        
    try:
        arr = np.frombuffer(data, dtype=dtype)
        
        # If it's a multiple of 128, it might be a 2D array of embeddings
        if elements % 128 == 0:
            num_embeddings = elements // 128
            if num_embeddings == 1:
                return arr.reshape((128,))
            else:
                return arr.reshape((num_embeddings, 128))
        else:
            # Fallback if somehow shape is completely different
            from utils.logger import logger
            logger.warning(f"Unexpected embedding size: {elements} elements. Storing flat.")
            return arr
    except Exception as e:
        from utils.logger import logger
        logger.error(f"Failed to deserialize embedding data: {e}")
        return None

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
