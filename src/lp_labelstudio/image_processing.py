import layoutparser as lp
from PIL import Image
import uuid
from paddleocr import PaddleOCR
import numpy as np
from typing import List, Dict, Any, Tuple

from lp_labelstudio.constants import PNG_EXTENSION

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')

def process_single_image(image_path: str, model: lp.models.Detectron2LayoutModel) -> List[Dict[str, Any]]:
    if not image_path.lower().endswith(PNG_EXTENSION):
        raise ValueError(f"The file '{image_path}' is not a PNG image.")

    image = Image.open(image_path)
    layout = model.detect(image)

    result = []
    for block in layout:
        coordinates = block.block.coordinates
        bbox = list(coordinates) if isinstance(coordinates, tuple) else coordinates.tolist()
        
        # Perform OCR on the block
        crop = image.crop(bbox)
        ocr_result = ocr.ocr(np.array(crop), cls=False)
        text = ' '.join([line[1][0] for line in ocr_result])
        
        result.append({
            'type': block.type,
            'score': float(block.score),
            'bbox': bbox,
            'text': text.strip()  # Add the OCR text to the result
        })

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
        "data": {"image": filename},
        "annotations": [{"result": annotations}]
    }
