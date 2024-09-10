import layoutparser as lp
from PIL import Image
import uuid
from typing import List, Dict, Any, Tuple

from .constants import PNG_EXTENSION

def process_single_image(image_path: str, model: lp.models.Detectron2LayoutModel) -> List[Dict[str, Any]]:
    """Process a single image and return the layout analysis results."""
    if not image_path.lower().endswith(PNG_EXTENSION):
        raise ValueError(f"The file '{image_path}' is not a PNG image.")

    image = Image.open(image_path)
    layout = model.detect(image)

    result = []
    for block in layout:
        coordinates = block.block.coordinates
        bbox = list(coordinates) if isinstance(coordinates, tuple) else coordinates.tolist()
        
        result.append({
            'type': block.type,
            'score': float(block.score),
            'bbox': bbox
        })

    return result

def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """Get the dimensions of an image."""
    with Image.open(image_path) as img:
        return img.size

def convert_to_label_studio_format(layout: List[Dict[str, Any]], img_width: int, img_height: int, filename: str) -> Dict[str, Any]:
    """Convert layout analysis results to Label Studio format."""
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
                "rectanglelabels": [block['type']]
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
