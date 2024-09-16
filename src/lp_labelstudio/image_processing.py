from typing import List, Dict, Any, Tuple
import logging
import uuid
import numpy as np
from PIL import Image
import layoutparser as lp  # type: ignore
from paddleocr import PaddleOCR  # type: ignore

from lp_labelstudio.constants import JPEG_EXTENSION

logger = logging.getLogger(__name__)

# Initialize PaddleOCR
ocr: PaddleOCR = PaddleOCR(lang='it')

def process_single_image(image_path: str, model: lp.models.Detectron2LayoutModel) -> List[Dict[str, Any]]:
    logger.info(f"Processing image: {image_path}")
    image: Image.Image = Image.open(image_path)
    layout: List[lp.elements.layout_element.BaseLayoutElement] = model.detect(image)

    result: List[Dict[str, Any]] = []
    for i, block in enumerate(layout):
        # Perform OCR on the block
        crop: Image.Image = image.crop(tuple(map(int, block.block.coordinates)))
        ocr_result: List[List[Tuple[List[List[int]], Tuple[str, float]]]] = ocr.ocr(np.array(crop), cls=False)

        if ocr_result is None or not ocr_result[0]:
            logger.warning(f"OCR result is empty for block {i} in {image_path}")
            text = ""
        else:
            text = ' '.join([line[1][0] for line in ocr_result[0]])

        result.append({
            'type': block.type,
            'score': float(block.score),
            'bbox': block.block.coordinates,
            'text': text.strip()  # Add the OCR text to the result
        })

    logger.info(f"Processed {len(result)} blocks in {image_path}")
    return result

def get_image_size(image_path: str) -> Tuple[int, int]:
    with Image.open(image_path) as img:
        return img.size

def convert_to_label_studio_format(layout: List[Dict[str, Any]], img_width: int, img_height: int, filename: str) -> Dict[str, Any]:
    annotations = []
    for block in layout:
        bbox = block['bbox']
        annotation = {
            "value": {
                "x": bbox[0] / img_width * 100,
                "y": bbox[1] / img_height * 100,
                "width": (bbox[2] - bbox[0]) / img_width * 100,
                "height": (bbox[3] - bbox[1]) / img_height * 100,
                "rotation": 0,
                "rectanglelabels": [block['type']],
                "transcription": block['text']  # Add the OCR text to the annotation
            },
            "type": "rectanglelabels",
            "id": str(uuid.uuid4()),
            "from_name": "label",
            "to_name": "image",
            "image_rotation": 0
        }
        annotations.append(annotation)

    return {
        "data": {"ocr": filename},
        "predictions": [annotations],
    }
