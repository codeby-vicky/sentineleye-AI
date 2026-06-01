import easyocr
import numpy as np
import time
from dataclasses import dataclass
from typing import List, Tuple
from utils.logger import logger
from utils.gpu_utils import get_gpu_info

@dataclass
class ExtractedText:
    full_text: str
    blocks: List[Tuple[str, float, Tuple[int, int, int, int]]]  # text, conf, bbox
    extraction_time: float

class TextExtractor:
    def __init__(self):
        logger.info("Initializing EasyOCR Text Extractor...")
        gpu_info = get_gpu_info()
        use_gpu = gpu_info['pytorch_cuda']
        
        # Initialize EasyOCR reader (downloads model on first run if needed)
        # We only need English for this project
        self.reader = easyocr.Reader(['en'], gpu=use_gpu)
        logger.info(f"EasyOCR initialized (GPU: {use_gpu})")

    def extract(self, image: np.ndarray) -> ExtractedText:
        """
        Extract text from an image.
        """
        start_time = time.time()
        blocks = []
        full_text = ""
        
        if image is None or image.size == 0:
            return ExtractedText("", [], 0.0)
            
        try:
            # EasyOCR expects RGB or grayscale
            # But it can handle BGR directly as well. Let's pass BGR.
            results = self.reader.readtext(image)
            
            text_parts = []
            for (bbox, text, prob) in results:
                # bbox is [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                # Convert to (x, y, w, h)
                x = int(min([pt[0] for pt in bbox]))
                y = int(min([pt[1] for pt in bbox]))
                w = int(max([pt[0] for pt in bbox]) - x)
                h = int(max([pt[1] for pt in bbox]) - y)
                
                if prob > 0.3:  # Filter out low confidence gibberish
                    blocks.append((text, float(prob), (x, y, w, h)))
                    text_parts.append(text)
                    
            full_text = " ".join(text_parts)
            
        except Exception as e:
            logger.error(f"Error during OCR extraction: {e}")
            
        extraction_time = time.time() - start_time
        return ExtractedText(full_text, blocks, extraction_time)
