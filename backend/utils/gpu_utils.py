from utils.logger import logger

def get_gpu_info():
    """Check for CUDA and return GPU information."""
    info = {
        'has_cuda': False,
        'pytorch_cuda': False,
        'opencv_cuda': False,
        'device_name': 'CPU',
        'details': ''
    }
    
    try:
        import torch
        info['pytorch_cuda'] = torch.cuda.is_available()
        if info['pytorch_cuda']:
            info['has_cuda'] = True
            info['device_name'] = torch.cuda.get_device_name(0)
            mem_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            allocated_mb = torch.cuda.memory_allocated(0) / 1e6
            reserved_mb = torch.cuda.memory_reserved(0) / 1e6
            
            # RTX 2050 has 4GB, usable is typically ~3.5GB due to OS overhead
            usable_gb = mem_gb * 0.85 
            
            info['details'] += f"\nGPU: {info['device_name']}\n"
            info['details'] += f"Total VRAM: {mem_gb:.1f} GB\n"
            info['details'] += f"Estimated usable: ~{usable_gb:.1f} GB\n"
            info['details'] += f"Current AI allocation: {allocated_mb:.1f} MB\n"
            info['details'] += f"Reserved: {reserved_mb:.1f} MB\n"
    except ImportError:
        logger.warning("PyTorch not installed.")
        
    try:
        import cv2
        cuda_count = cv2.cuda.getCudaEnabledDeviceCount() if hasattr(cv2, 'cuda') else 0
        info['opencv_cuda'] = cuda_count > 0
        if info['opencv_cuda']:
            info['has_cuda'] = True
            info['details'] += f"OpenCV has {cuda_count} CUDA devices. "
    except ImportError:
        logger.warning("OpenCV not installed.")
        
    if not info['has_cuda']:
        info['details'] = "Running on CPU only."
        
    logger.info(f"GPU Status: {info['details']}")
    return info
