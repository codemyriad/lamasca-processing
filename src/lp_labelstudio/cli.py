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

@cli.command()
@click.argument('image_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
def process_newspaper(image_path):
    """Process a newspaper image using layoutparser with a newspaper model."""
    click.echo(f"Processing newspaper image: {image_path}")
    
    try:
        # Load the image
        image = lp.io.load_image(image_path)
    
        # Initialize layoutparser model for newspapers
        model = lp.models.Detectron2LayoutModel('lp://NewspaperNavigator/faster_rcnn_R_50_FPN_3x/config',
                                                 extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
                                                 label_map={1: "Photograph", 2: "Illustration", 3: "Map", 
                                                            4: "Comics/Cartoon", 5: "Editorial Cartoon", 
                                                            6: "Headline", 7: "Advertisement", 8: "Text"})
    
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
        click.echo(f"Error processing newspaper image: {str(e)}", err=True)

if __name__ == '__main__':
    cli()
