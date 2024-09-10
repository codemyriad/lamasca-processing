import click
import layoutparser as lp
from PIL import Image
import json
import os

def process_single_image(image_path, model):
    """Process a single image and return the layout."""
    if not image_path.lower().endswith('.png'):
        raise ValueError(f"The file '{image_path}' is not a PNG image.")

    # Load the image
    image = Image.open(image_path)

    # Detect layout
    layout = model.detect(image)

    # Convert layout to JSON-serializable format
    result = []
    for block in layout:
        coordinates = block.block.coordinates
        if isinstance(coordinates, tuple):
            bbox = list(coordinates)
        else:
            bbox = coordinates.tolist()
        
        result.append({
            'type': block.type,
            'score': float(block.score),
            'bbox': bbox
        })

    return result

@click.group()
def cli():
    """LP-LabelStudio CLI tool."""
    pass

@cli.command()
@click.argument('image_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--redo', is_flag=True, help='Reprocess and replace existing annotations')
def process_image(image_path, redo):
    """Process a single PNG image using layoutparser."""
    click.echo(f"Processing image: {image_path}")

    output_path = os.path.splitext(image_path)[0] + '_annotations.json'
    if os.path.exists(output_path) and not redo:
        click.echo(f"Skipping {image_path} - annotation file already exists. Use --redo to reprocess.")
        return

    try:
        # Initialize layoutparser model
        model = lp.models.Detectron2LayoutModel('lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config')
        
        # Process the image
        result = process_single_image(image_path, model)

        # Output result as JSON
        click.echo(json.dumps(result, indent=2))

        # Save annotations
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        click.echo(f"Annotations saved to {output_path}")
    except Exception as e:
        click.echo(f"Error processing image: {str(e)}", err=True)

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--redo', is_flag=True, help='Reprocess and replace existing annotations')
def process_newspaper(directory, redo):
    """Process newspaper pages (PNG images) in a directory using layoutparser and convert to Label Studio format."""
    import uuid
    import os

    click.echo(f"Processing newspaper pages in directory: {directory}")

    # Initialize layoutparser model
    model = lp.models.Detectron2LayoutModel('lp://NewspaperNavigator/faster_rcnn_R_50_FPN_3x/config')

    for filename in os.listdir(directory):
        if filename.lower().endswith('.png'):
            image_path = os.path.join(directory, filename)
            output_path = os.path.splitext(image_path)[0] + '_annotations.json'
            
            # Skip if annotation file already exists and --redo is not set
            if os.path.exists(output_path) and not redo:
                click.echo(f"Skipping {filename} - annotation file already exists")
                continue
            
            click.echo(f"Processing page: {image_path}")

            try:
                # Process the image
                layout = process_single_image(image_path, model)

                # Load the image to get dimensions
                with Image.open(image_path) as img:
                    img_width, img_height = img.size

                # Convert layout to Label Studio format
                annotations = []
                for block in layout:
                    bbox = block['bbox']

                    annotation = {
                        "value": {
                            "x": bbox[0] / img_width * 100,  # Convert to percentage
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
                with open(output_path, 'w') as f:
                    json.dump(label_studio_data, f, indent=2)

                click.echo(f"Label Studio annotations saved to {output_path}")
            except Exception as e:
                click.echo(f"Error processing image {filename}: {str(e)}", err=True)

    click.echo("Processing complete.")

def main():
    cli()

if __name__ == '__main__':
    main()
