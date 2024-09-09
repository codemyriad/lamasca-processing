import click
import layoutparser as lp
from PIL import Image
import json
import uuid
import os
import cv2
import numpy as np

@click.group()
def cli():
    """LP-LabelStudio CLI tool."""
    pass

@cli.command()
def hello():
    """Simple command that says hello."""
    click.echo("Hello from lp-labelstudio!")

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
def process_dir(directory):
    """Process a directory of images."""
    click.echo(f"Processing directory: {directory}")
    # TODO: Implement directory processing logic

@cli.command()
@click.argument('image_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
def process_image(image_path):
    """Process a single PNG image using layoutparser."""
    if not image_path.lower().endswith('.png'):
        click.echo(f"Error: The file '{image_path}' is not a PNG image.", err=True)
        return

    click.echo(f"Processing image: {image_path}")
    
    try:
        # Load the image
        image = Image.open(image_path)
    
        # Initialize layoutparser model
        model = lp.models.Detectron2LayoutModel('lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config')
    
        # Detect layout
        layout = model.detect(image)
    
        # Convert layout to JSON-serializable format
        result = []
        for block in layout:
            result.append({
                'type': block.type,
                'score': float(block.score),
                'bbox': block.block.coordinates.tolist()
            })
    
        # Output result as JSON
        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(f"Error processing image: {str(e)}", err=True)

@cli.command('process_newspaper')
@click.argument('image_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--output', '-o', type=click.Path(file_okay=True, dir_okay=False), default='label_studio_annotations.json', help='Output JSON file for Label Studio')
def process_newspaper(image_path, output):
    """Process a newspaper image using layoutparser and convert to Label Studio format."""
    click.echo(f"Processing newspaper image: {image_path}")
    
    try:
        # Load the image using cv2
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Convert the image to a PIL Image object
        pil_image = Image.fromarray(image)
    
        # Initialize layoutparser model for newspapers
        model = lp.models.Detectron2LayoutModel('lp://NewspaperNavigator/faster_rcnn_R_50_FPN_3x/config',
                                                 extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
                                                 label_map={1: "Photograph", 2: "Illustration", 3: "Map", 
                                                            4: "Comics/Cartoon", 5: "Editorial Cartoon", 
                                                            6: "Headline", 7: "Advertisement", 8: "Text"})
    
        # Detect layout
        layout = model.detect(pil_image)
    
        # Convert layout to Label Studio format
        annotations = []
        for block in layout:
            bbox = block.block.coordinates
            annotation = {
                "value": {
                    "x": bbox[0] / pil_image.width * 100,  # Convert to percentage
                    "y": bbox[1] / pil_image.height * 100,
                    "width": (bbox[2] - bbox[0]) / pil_image.width * 100,
                    "height": (bbox[3] - bbox[1]) / pil_image.height * 100,
                    "rotation": 0,
                    "rectanglelabels": [block.type]
                },
                "type": "rectanglelabels",
                "id": str(uuid.uuid4()),
                "from_name": "label",
                "to_name": "image",
                "image_rotation": 0
            }
            annotations.append(annotation)

        label_studio_data = {
            "data": {
                "image": os.path.basename(image_path)
            },
            "annotations": [
                {
                    "result": annotations
                }
            ]
        }

        # Write to JSON file for Label Studio
        with open(output, 'w') as f:
            json.dump(label_studio_data, f, indent=2)

        click.echo(f"Label Studio annotations saved to {output}")
    except Exception as e:
        click.echo(f"Error processing newspaper image: {str(e)}", err=True)

if __name__ == '__main__':
    cli()
