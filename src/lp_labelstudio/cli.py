import click
import layoutparser as lp
from PIL import Image
import json
import os
import logging
import uuid
from typing import List, Dict, Any, Tuple

from lp_labelstudio.constants import PNG_EXTENSION, PUBLAYNET_MODEL_PATH, NEWSPAPER_MODEL_PATH
from lp_labelstudio.image_processing import process_single_image, convert_to_label_studio_format, get_image_dimensions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_annotations(output_path: str, data: Any) -> None:
    """Save annotations to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Annotations saved to {output_path}")

@click.group()
def cli():
    """LP-LabelStudio CLI tool."""
    pass

@cli.command()
@click.argument('image_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--redo', is_flag=True, help='Reprocess and replace existing annotations')
def process_image(image_path: str, redo: bool) -> None:
    """Process a single PNG image using layoutparser."""
    output_path = os.path.splitext(image_path)[0] + '_annotations.json'
    if os.path.exists(output_path) and not redo:
        click.echo(click.style(f"Skipped {image_path} (annotation file exists)", fg="yellow"))
        return

    model = lp.models.Detectron2LayoutModel(PUBLAYNET_MODEL_PATH)
    result = process_single_image(image_path, model)
    save_annotations(output_path, result)
    
    # Get image dimensions
    img_width, img_height = get_image_dimensions(image_path)
    
    # Count the types of layout elements
    element_counts = {}
    for element in result:
        element_type = element['type']
        element_counts[element_type] = element_counts.get(element_type, 0) + 1
    
    click.echo(click.style(f"Processed {image_path}:", fg="green", bold=True))
    click.echo(f"Image dimensions: {img_width}x{img_height}")
    click.echo(click.style(f"Total layout elements detected: {len(result)}", fg="cyan"))
    for element_type, count in element_counts.items():
        click.echo(f"  - {element_type}: {click.style(str(count), fg='bright_cyan')}")

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--redo', is_flag=True, help='Reprocess and replace existing annotations')
def process_newspaper(directory: str, redo: bool) -> None:
    """Process newspaper pages (PNG images) in a directory using layoutparser and convert to Label Studio format."""
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
            except ValueError as e:
                logger.error(f"ValueError processing image {filename}: {str(e)}")
            except IOError as e:
                logger.error(f"IOError processing image {filename}: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error processing image {filename}: {str(e)}")

    logger.info("Processing complete.")

def main():
    cli()

if __name__ == '__main__':
    main()
