import click
import layoutparser as lp
from PIL import Image
import json
import os
import logging
import uuid
from typing import List, Dict, Any

# Constants
PNG_EXTENSION = '.png'
PUBLAYNET_MODEL_PATH = 'lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config'
NEWSPAPER_MODEL_PATH = 'lp://NewspaperNavigator/faster_rcnn_R_50_FPN_3x/config'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_single_image(image_path: str, model: lp.models.Detectron2LayoutModel) -> List[Dict[str, Any]]:
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

def save_annotations(output_path: str, data: Any) -> None:
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Annotations saved to {output_path}")

def get_image_dimensions(image_path: str) -> tuple:
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

@click.group()
def cli():
    """LP-LabelStudio CLI tool."""
    pass

@cli.command()
@click.argument('image_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--redo', is_flag=True, help='Reprocess and replace existing annotations')
def process_image(image_path: str, redo: bool):
    """Process a single PNG image using layoutparser."""
    output_path = os.path.splitext(image_path)[0] + '_annotations.json'
    if os.path.exists(output_path) and not redo:
        click.echo(f"Skipped {image_path} (annotation file exists)")
        return

    model = lp.models.Detectron2LayoutModel(PUBLAYNET_MODEL_PATH)
    result = process_single_image(image_path, model)
    save_annotations(output_path, result)
    click.echo(f"Processed {image_path}: {len(result)} layout elements detected")

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--redo', is_flag=True, help='Reprocess and replace existing annotations')
def process_newspaper(directory: str, redo: bool):
    """Process newspaper pages (PNG images) in a directory using layoutparser and convert to Label Studio format."""
    import uuid

    logger.info(f"Processing newspaper pages in directory: {directory}")
    model = lp.models.Detectron2LayoutModel(NEWSPAPER_MODEL_PATH)

    for filename in os.listdir(directory):
        if filename.lower().endswith(PNG_EXTENSION):
            image_path = os.path.join(directory, filename)
            output_path = os.path.splitext(image_path)[0] + '_annotations.json'
            
            if os.path.exists(output_path) and not redo:
                logger.info(f"Skipping {filename} - annotation file already exists")
                continue
            
            logger.info(f"Processing page: {image_path}")

            try:
                layout = process_single_image(image_path, model)
                img_width, img_height = get_image_dimensions(image_path)
                label_studio_data = convert_to_label_studio_format(layout, img_width, img_height, filename)
                save_annotations(output_path, label_studio_data)
            except Exception as e:
                logger.error(f"Error processing image {filename}: {str(e)}")

    logger.info("Processing complete.")

def main():
    cli()

if __name__ == '__main__':
    main()
