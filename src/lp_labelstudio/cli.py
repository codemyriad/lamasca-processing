import click
import layoutparser as lp
from PIL import Image
import json
import uuid
import os
import cv2
import numpy as np
from PIL import Image, ImageOps
import warnings

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
        model = lp.models.Detectron2LayoutModel('lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config')
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

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
def process_newspaper(directory):
    """Process newspaper pages (PNG images) in a directory using layoutparser and convert to Label Studio format."""
    click.echo(f"Processing newspaper pages in directory: {directory}")

    # Initialize layoutparser model
    model = lp.models.Detectron2LayoutModel('lp://NewspaperNavigator/faster_rcnn_R_50_FPN_3x/config')

    for filename in os.listdir(directory):
        if filename.lower().endswith('.png'):
            image_path = os.path.join(directory, filename)
            click.echo(f"Processing page: {image_path}")

            # Load the image using PIL
            image = Image.open(image_path)

            # Detect layout
            layout = model.detect(image)

            # Convert layout to Label Studio format
            annotations = []
            for block in layout:
                bbox = block.block.coordinates
                annotation = {
                    "value": {
                        "x": bbox[0] / image.width * 100,  # Convert to percentage
                        "y": bbox[1] / image.height * 100,
                        "width": (bbox[2] - bbox[0]) / image.width * 100,
                        "height": (bbox[3] - bbox[1]) / image.height * 100,
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
                    "image": filename
                },
                "annotations": [
                    {
                        "result": annotations
                    }
                ]
            }

            # Write to JSON file next to the original image
            output_path = os.path.splitext(image_path)[0] + '_annotations.json'
            with open(output_path, 'w') as f:
                json.dump(label_studio_data, f, indent=2)

            click.echo(f"Label Studio annotations saved to {output_path}")

    click.echo("Processing complete.")

def main():
    cli()

if __name__ == '__main__':
    main()
