import click
import layoutparser as lp
import json
import os
import logging
from typing import Any, Dict, List

from lp_labelstudio.constants import PNG_EXTENSION, PUBLAYNET_MODEL_PATH, NEWSPAPER_MODEL_PATH
from lp_labelstudio.image_processing import process_single_image, convert_to_label_studio_format, get_image_size

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_annotations(output_path: str, data: Dict[str, Any]) -> None:
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Annotations saved to {output_path}")

def generate_summary(image_path: str, result: List[Dict[str, Any]], output_path: str) -> str:
    img_width, img_height = get_image_size(image_path)
    
    element_counts: Dict[str, int] = {}
    for element in result:
        element_type = element['type']
        element_counts[element_type] = element_counts.get(element_type, 0) + 1
    
    summary = click.style(f"Processed ", fg="green")
    summary += click.style(f"{image_path}", fg="bright_blue")
    summary += click.style(f" ({img_width}x{img_height}): ", fg="green")
    summary += click.style(f"{len(result)}", fg="yellow")
    summary += click.style(" elements detected (", fg="green")
    summary += ", ".join([f"{click.style(element_type, fg='cyan')}: {click.style(str(count), fg='yellow')}" for element_type, count in element_counts.items()])
    summary += click.style("). Annotations saved to: ", fg="green")
    summary += click.style(f"{output_path}", fg="bright_blue")
    return summary

@click.group()
def cli():
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

    click.echo(click.style(f"Processing {image_path}...", fg="blue"))
    
    model = lp.models.Detectron2LayoutModel(PUBLAYNET_MODEL_PATH)
    result = process_single_image(image_path, model)
    save_annotations(output_path, result)
    
    summary = generate_summary(image_path, result, output_path)
    click.echo(summary)

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
                click.echo(click.style(f"Skipped {image_path} (annotation file exists)", fg="yellow"))
                continue
            
            click.echo(click.style(f"Processing {image_path}...", fg="blue"))

            try:
                layout = process_single_image(image_path, model)
                img_width, img_height = get_image_size(image_path)
                label_studio_data = convert_to_label_studio_format(layout, img_width, img_height, filename)
                save_annotations(output_path, label_studio_data)
                
                summary = generate_summary(image_path, layout, output_path)
                click.echo(summary)
            except ValueError as e:
                click.echo(click.style(f"ValueError processing image {filename}: {str(e)}", fg="red"))
            except IOError as e:
                click.echo(click.style(f"IOError processing image {filename}: {str(e)}", fg="red"))
            except Exception as e:
                click.echo(click.style(f"Unexpected error processing image {filename}: {str(e)}", fg="red"))

    click.echo(click.style("Processing complete.", fg="green"))

def main() -> None:
    cli()

if __name__ == '__main__':
    main()
