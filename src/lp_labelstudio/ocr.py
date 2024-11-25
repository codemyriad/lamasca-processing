from typing import List, Tuple, Optional
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR


def ocr_box(
    img: Image.Image,
    box: Tuple[int, int, int, int],
    target_dpi: int = 150,  # Target DPI for OCR processing
) -> List[Tuple[List[float], Tuple[str, float]]]:
    """
    Perform OCR on a specific region of an image, with resolution adjustment.

    Args:
        img: PIL Image to process
        box: Tuple of (x, y, width, height) defining the region to process
        target_dpi: Target DPI for OCR processing. Original image will be scaled
                   to this resolution for processing, but coordinates will be
                   returned in the original resolution.

    Returns:
        List of tuples containing:
        - List of coordinates [x1, y1, x2, y2] in original image coordinates
        - Tuple of (text, confidence)
    """
    x, y, width, height = box

    # Crop the image to the region
    region_img = img.crop((x, y, x + width, y + height))

    # Get current DPI (assuming standard 300 DPI if not specified)
    # Store it as a global for future ratio-based calculations
    current_dpi = region_img.info.get("dpi", (300, 300))[0]
    if "current_dpi" not in OCR_CACHE:
        OCR_CACHE["current_dpi"] = current_dpi

    # Calculate scale factor
    scale_factor = target_dpi / current_dpi

    # Scale the image
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    scaled_img = region_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Run OCR on the scaled image
    ocr_result = get_ocr().ocr(np.array(scaled_img), cls=True, rec=True)

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
    ocr = OCR_CACHE.get("ocr")
    if not ocr:
        ocr = OCR_CACHE["ocr"] = PaddleOCR(
            use_angle_cls=False,
            lang="it",
            rec_algorithm="SVTR_LCNet",
            det_db_box_thresh=0.1,
        )
    return ocr
