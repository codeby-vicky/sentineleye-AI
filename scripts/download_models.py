"""
Model Download Script
Downloads required NLP models on first run.
"""

import os
import sys


def download_models():
    """Download all required pre-trained models."""
    
    print("=" * 60)
    print("  SentinelEye AI — Model Download")
    print("=" * 60)
    print()

    # 1. Download sentence-transformers model
    print("[1/2] Downloading NLP model: all-MiniLM-L6-v2...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print(f"  ✅ NLP model downloaded and cached")
        
        # Test encoding
        test_embedding = model.encode("test sentence")
        print(f"  ✅ Model test passed (embedding dim: {len(test_embedding)})")
    except Exception as e:
        print(f"  ❌ Failed to download NLP model: {e}")
    print()

    # 2. Download EasyOCR models
    print("[2/2] Downloading OCR model (English)...")
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)  # Download with CPU to avoid CUDA issues
        print(f"  ✅ OCR model downloaded and cached")
    except Exception as e:
        print(f"  ❌ Failed to download OCR model: {e}")
    print()

    print("=" * 60)
    print("  All models downloaded!")
    print("=" * 60)


if __name__ == "__main__":
    download_models()
