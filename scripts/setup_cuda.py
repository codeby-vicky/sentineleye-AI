"""
CUDA GPU Setup Verification Script
Run this to check if your system has proper CUDA support.
"""

import sys

def check_cuda():
    """Check CUDA availability across all frameworks used in the project."""
    
    print("=" * 60)
    print("  SentinelEye AI — CUDA GPU Verification")
    print("=" * 60)
    print()

    # 1. Check Python version
    print(f"[INFO] Python version: {sys.version}")
    print()

    # 2. Check PyTorch CUDA
    print("[CHECK] PyTorch CUDA Support...")
    try:
        import torch
        print(f"  PyTorch version: {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  CUDA version: {torch.version.cuda}")
            print(f"  GPU device: {torch.cuda.get_device_name(0)}")
            print(f"  GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
            print(f"  ✅ PyTorch CUDA — READY")
        else:
            print(f"  ⚠️  PyTorch CUDA not available. OCR and NLP will run on CPU.")
    except ImportError:
        print("  ❌ PyTorch not installed.")
    print()

    # 3. Check OpenCV
    print("[CHECK] OpenCV...")
    try:
        import cv2
        print(f"  OpenCV version: {cv2.__version__}")
        cuda_count = cv2.cuda.getCudaEnabledDeviceCount() if hasattr(cv2, 'cuda') else 0
        print(f"  CUDA devices: {cuda_count}")
        if cuda_count > 0:
            print(f"  ✅ OpenCV CUDA — READY")
        else:
            print(f"  ℹ️  OpenCV running on CPU (normal for pip install)")
    except ImportError:
        print("  ❌ OpenCV not installed.")
    print()

    # 4. Check MediaPipe
    print("[CHECK] MediaPipe...")
    try:
        import mediapipe as mp
        print(f"  MediaPipe version: {mp.__version__}")
        print(f"  ℹ️  MediaPipe runs on CPU on Windows Python (30+ FPS)")
        print(f"  ✅ MediaPipe — READY")
    except ImportError:
        print("  ❌ MediaPipe not installed.")
    print()

    # 5. Check face_recognition
    print("[CHECK] face_recognition...")
    try:
        import face_recognition
        import dlib
        print(f"  dlib version: {dlib.__version__}")
        print(f"  dlib CUDA: {dlib.DLIB_USE_CUDA}")
        if dlib.DLIB_USE_CUDA:
            print(f"  ✅ face_recognition with CUDA — READY")
        else:
            print(f"  ℹ️  face_recognition running on CPU (HOG model)")
            print(f"  ✅ face_recognition — READY")
    except ImportError:
        print("  ❌ face_recognition not installed.")
    print()

    # 6. Check EasyOCR
    print("[CHECK] EasyOCR...")
    try:
        import easyocr
        print(f"  EasyOCR version: {easyocr.__version__ if hasattr(easyocr, '__version__') else 'installed'}")
        import torch
        if torch.cuda.is_available():
            print(f"  ✅ EasyOCR will use GPU (PyTorch CUDA)")
        else:
            print(f"  ℹ️  EasyOCR will use CPU")
    except ImportError:
        print("  ❌ EasyOCR not installed.")
    print()

    # 7. Check sentence-transformers
    print("[CHECK] sentence-transformers...")
    try:
        import sentence_transformers
        print(f"  Version: {sentence_transformers.__version__}")
        import torch
        if torch.cuda.is_available():
            print(f"  ✅ sentence-transformers will use GPU")
        else:
            print(f"  ℹ️  sentence-transformers will use CPU")
    except ImportError:
        print("  ❌ sentence-transformers not installed.")
    print()

    # 8. Check mss (screen capture)
    print("[CHECK] Screen Capture (mss)...")
    try:
        import mss
        print(f"  mss version: {mss.__version__}")
        with mss.mss() as sct:
            monitors = sct.monitors
            print(f"  Monitors detected: {len(monitors) - 1}")
            for i, m in enumerate(monitors[1:], 1):
                print(f"    Monitor {i}: {m['width']}x{m['height']}")
        print(f"  ✅ Screen Capture — READY")
    except ImportError:
        print("  ❌ mss not installed.")
    print()

    print("=" * 60)
    print("  Verification Complete")
    print("=" * 60)


if __name__ == "__main__":
    check_cuda()
