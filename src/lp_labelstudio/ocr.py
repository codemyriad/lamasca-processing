from typing import List, Tuple, Optional
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

def ocr_box(
    img: Image.Image,
    box: Tuple[int, int, int, int],
) -> List[Tuple[List[float], Tuple[str, float]]]:
    """
    Perform OCR on a specific region of an image.

    Args:
        img: PIL Image to process
        box: Tuple of (x, y, width, height) defining the region to process
        ocr: Optional PaddleOCR instance. If None, creates a new instance.

    Returns:
        List of tuples containing:
        - List of coordinates [x1, y1, x2, y2]
        - Tuple of (text, confidence)
    """
    x, y, width, height = box

    # Crop the image to the region
    region_img = img.crop((x, y, x + width, y + height))

    # Run OCR on the cropped area
    ocr_result = get_ocr().ocr(np.array(region_img), cls=True, rec=True)

    results = []
    if ocr_result and ocr_result[0]:
        for line in ocr_result[0]:
            text, confidence = line[1]
            abs_bbox = [x, y, x + width, y + height]

            results.append((abs_bbox, (text, confidence)))

    return results

OCR_CACHE = {}

def get_ocr():
    """
    Cache the ocr object so that we instantiate at most one per invocation
    """
    ocr = OCR_CACHE.get('ocr')
    if not ocr:
        ocr = OCR_CACHE["ocr"] = PaddleOCR(
            use_angle_cls=True,
            lang="fr",
            rec_algorithm="SVTR_LCNet",
            det_db_box_thresh=0.3
        )
    return ocr
