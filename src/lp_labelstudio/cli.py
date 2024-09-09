import click
import layoutparser as lp
from PIL import Image
import json

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
    click.echo(f"Processing image: {image_path}")
    
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

if __name__ == '__main__':
    cli()
