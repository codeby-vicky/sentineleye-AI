import numpy as np
from datetime import datetime, timezone

def numpy_to_bytes(arr: np.ndarray) -> bytes:
    """Serialize a numpy array to bytes for database storage.
    Stores shape metadata as a header so we can reconstruct any dimension."""
    import struct
    # Header: ndim (1 byte) + each dim (4 bytes each) + dtype char length (1 byte) + dtype string
    ndim = arr.ndim
    shape = arr.shape
    dtype_str = str(arr.dtype).encode('utf-8')
    
    # Pack: [ndim:1B] [dim0:4B] [dim1:4B] ... [dtype_len:1B] [dtype:NB] [data]
    header = struct.pack('B', ndim)
    for d in shape:
        header += struct.pack('I', d)
    header += struct.pack('B', len(dtype_str))
    header += dtype_str
    
    return header + arr.tobytes()

def bytes_to_numpy(data: bytes, dtype=np.float64) -> np.ndarray:
    """Deserialize bytes from database to a numpy array.
    Supports both new format (with header) and legacy format (raw float64 bytes)."""
    if not data:
        return np.array([])
    
    import struct
    
    try:
        # Try new format first: read header
        offset = 0
        ndim = struct.unpack_from('B', data, offset)[0]
        offset += 1
        
        # Sanity check: ndim should be 1 or 2 for embeddings
        if ndim in (1, 2) and len(data) > (1 + ndim * 4 + 1):
            shape = []
            for _ in range(ndim):
                dim = struct.unpack_from('I', data, offset)[0]
                shape.append(dim)
                offset += 4
            
            dtype_len = struct.unpack_from('B', data, offset)[0]
            offset += 1
            
            if dtype_len > 0 and dtype_len < 20 and offset + dtype_len <= len(data):
                dtype_str = data[offset:offset + dtype_len].decode('utf-8')
                offset += dtype_len
                
                arr_data = data[offset:]
                actual_dtype = np.dtype(dtype_str)
                expected_bytes = int(np.prod(shape)) * actual_dtype.itemsize
                
                if len(arr_data) == expected_bytes:
                    arr = np.frombuffer(arr_data, dtype=actual_dtype)
                    return arr.reshape(shape)
        
        # Fall through to legacy format
    except Exception:
        pass
    
    # Legacy format: raw float64 bytes, auto-detect shape
    elements = len(data) // 8
    if elements == 0:
        return np.array([])
    
    try:
        arr = np.frombuffer(data, dtype=np.float64)
        
        # Try 512-d first (InsightFace), then 128-d (dlib)
        if elements % 512 == 0 and elements >= 512:
            num_embeddings = elements // 512
            if num_embeddings == 1:
                return arr.reshape((512,))
            else:
                return arr.reshape((num_embeddings, 512))
        elif elements % 128 == 0:
            num_embeddings = elements // 128
            if num_embeddings == 1:
                return arr.reshape((128,))
            else:
                return arr.reshape((num_embeddings, 128))
        else:
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
