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

# Make coordinates reading readable
X1, Y1, X2, Y2 = 0, 1, 2, 3

def process_single_image(image_path: str, model: lp.models.Detectron2LayoutModel) -> List[Dict[str, Any]]:
    """Returns a list of annotations suitable for Label Studio from a single image.
    """
    logger.info(f"Processing image: {image_path}")
    image: Image.Image = Image.open(image_path)
    layout: List[lp.elements.layout_element.BaseLayoutElement] = model.detect(image)

    result: List[Dict[str, Any]] = []
    template = {
        "original_width": image.width,
        "original_height": image.height,
        "image_rotation": 0,
        "to_name": "image",
    }
    for i, block in enumerate(layout):
        # Add the block and the labels to result
        x_percentage = (block.coordinates[X1] / image.width) * 100
        y_percentage = (block.coordinates[Y1] / image.height) * 100
        width_percentage = ((block.coordinates[X2] - block.coordinates[X1]) / image.width) * 100
        height_percentage = ((block.coordinates[Y2] - block.coordinates[Y1]) / image.height) * 100

        block_template = dict(template, **{
            "id": f"{i}",
            "value": {
                "x": x_percentage,
                "y": y_percentage,
                "width": width_percentage,
                "height": height_percentage,
                "rotation": 0
            },
        })
        result.append(dict(block_template, **{
            "from_name": "bbox",
            "type": "rectangle",
        }))
        result.append(dict(block_template, **{
            "from_name": "label",
            "type": "labels",
        }))
        result[-1]["value"]["labels"] = [block.type]
        # Perform OCR on the block
        crop: Image.Image = image.crop(tuple(map(int, block.block.coordinates)))
        ocr_result: List[List[Tuple[List[List[int]], Tuple[str, float]]]] = ocr.ocr(np.array(crop), cls=False)

        if ocr_result is not None and ocr_result[0]:
            text = ' '.join([line[1][0] for line in ocr_result[0]])
            result.append(dict(block_template, **{
                "from_name": "transcription",
                "type": "textarea",
            }))
            result[-1]["value"]["text"] = [text]

    logger.info(f"Processed {len(result)} blocks in {image_path}")
    return result

def get_image_size(image_path: str) -> Tuple[int, int]:
    with Image.open(image_path) as img:
        return img.size

def convert_to_label_studio_format(annotations: List[Dict[str, Any]], img_width: int, img_height: int, filename: str) -> Dict[str, Any]:
    return {
        "data": {"ocr": filename},
        "predictions": [annotations],
    }
