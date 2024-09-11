import click
import os
import logging
from typing import Any, Dict, List, Union
from lp_labelstudio.generate_manifest import generate_manifest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    pass

cli.add_command(generate_manifest)

@cli.command()
@click.argument('image_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--redo', is_flag=True, help='Reprocess and replace existing annotations')
def process_image(image_path: str, redo: bool) -> None:
    """Process a single JPEG image using layoutparser."""
    import json
    import layoutparser as lp  # type: ignore
    from lp_labelstudio.constants import NEWSPAPER_MODEL_PATH
    from lp_labelstudio.image_processing import process_single_image, get_image_size

    output_path = os.path.splitext(image_path)[0] + '_annotations.json'
    if os.path.exists(output_path) and not redo:
        click.echo(click.style(f"Skipped {image_path} (annotation file exists)", fg="yellow"))
        return

    click.echo(click.style(f"Processing {image_path}...", fg="blue"))

    model: lp.models.Detectron2LayoutModel = lp.models.Detectron2LayoutModel(NEWSPAPER_MODEL_PATH)
    result: List[Dict[str, Any]] = process_single_image(image_path, model)
    
    with open(output_path, 'w') as f:
        json.dump({"result": result}, f, indent=2)
    logger.info(f"Annotations saved to {output_path}")

    summary: str = generate_summary(image_path, result, output_path)
    click.echo(summary)

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--redo', is_flag=True, help='Reprocess and replace existing annotations')
def process_newspaper(directory: str, redo: bool) -> None:
    """Process newspaper pages (JPEG images) recursively in a directory using layoutparser and convert to Label Studio format."""
    import json
    import layoutparser as lp  # type: ignore
    from lp_labelstudio.constants import JPEG_EXTENSION, NEWSPAPER_MODEL_PATH
    from lp_labelstudio.image_processing import process_single_image, convert_to_label_studio_format, get_image_size

    logger.info(f"Processing newspaper pages recursively in directory: {directory}")
    model = lp.models.Detectron2LayoutModel(NEWSPAPER_MODEL_PATH)

    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith(JPEG_EXTENSION):
                image_path = os.path.join(root, filename)
                output_path = os.path.splitext(image_path)[0] + '_annotations.json'

                if os.path.exists(output_path) and not redo:
                    click.echo(click.style(f"Skipped {image_path} (annotation file exists)", fg="yellow"))
                    continue

                click.echo(click.style(f"Processing {image_path}...", fg="blue"))

                layout = process_single_image(image_path, model)
                img_width, img_height = get_image_size(image_path)
                label_studio_data = convert_to_label_studio_format(layout, img_width, img_height, filename)
                
                with open(output_path, 'w') as f:
                    json.dump(label_studio_data, f, indent=2)
                logger.info(f"Annotations saved to {output_path}")

                summary = generate_summary(image_path, layout, output_path)
                click.echo(summary)

    click.echo(click.style("Processing complete.", fg="green"))

def generate_summary(image_path: str, result: List[Dict[str, Any]], output_path: str) -> str:
    from lp_labelstudio.image_processing import get_image_size

    img_width, img_height = get_image_size(image_path)

    element_counts: Dict[str, int] = {}
    total_chars: int = 0
    for element in result:
        element_type: str = element['type']
        element_counts[element_type] = element_counts.get(element_type, 0) + 1
        total_chars += len(element['text'])

    summary = click.style(f"Processed ", fg="green")
    summary += click.style(f"{image_path}", fg="bright_blue")
    summary += click.style(f" ({img_width}x{img_height}): ", fg="green")
    summary += click.style(f"{len(result)}", fg="yellow")
    summary += click.style(" elements detected (", fg="green")
    summary += ", ".join([f"{click.style(element_type, fg='cyan')}: {click.style(str(count), fg='yellow')}" for element_type, count in element_counts.items()])
    summary += click.style(f"). Total characters: ", fg="green")
    summary += click.style(f"{total_chars}", fg="yellow")
    summary += click.style("). Annotations saved to: ", fg="green")
    summary += click.style(f"{output_path}", fg="bright_blue")
    return summary

def main() -> None:
    cli()

if __name__ == '__main__':
    main()
