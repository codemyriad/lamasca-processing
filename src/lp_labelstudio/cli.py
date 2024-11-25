import click
import os
import logging
import json
import numpy as np
from typing import Any, Dict, List, Union, Tuple, Optional
from rich import print as rprint
from rich.table import Table
from rich.console import Console
from pathlib import Path
from PIL import Image
from lp_labelstudio.generate_manifest import generate_labelstudio_manifest
from lp_labelstudio.escriptorium_cli import escriptorium as escriptorium_group
from lp_labelstudio.labelstudio_api import labelstudio_api
from lp_labelstudio.collect_coco import collect_coco
from lp_labelstudio.generate_thumbnails import generate_thumbnails
from lp_labelstudio.constants import (
    JPEG_EXTENSION,
    NEWSPAPER_MODEL_PATH,
    NEWSPAPER_LABEL_MAP,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    pass


cli.command(generate_labelstudio_manifest)


@cli.command(name="generate-index-txt")
@click.argument(
    "directories",
    nargs=-1,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
@click.option("--replace-from", required=True, help="The path prefix to replace")
@click.option("--replace-to", required=True, help="The URL prefix to replace with")
def cli_generate_index_txt(
    directories: List[str], replace_from: str, replace_to: str
) -> None:
    """Generate index.txt files containing full URLs of JPEG files in the given directories."""
    # We import here for performance reasons. Don't move up!
    from lp_labelstudio.generate_index_txt import generate_index_txt

    generate_index_txt(directories, replace_from, replace_to)


@cli.command()
@click.argument(
    "image_path_string", type=click.Path(exists=True, file_okay=True, dir_okay=False)
)
@click.option("--redo", is_flag=True, help="Reprocess and replace existing annotations")
def process_image(image_path_string: str, redo: bool) -> None:
    """Process a single JPEG image. Perform OCR for the areas found in annotations and generate ALTO XML"""
    image_path = Path(image_path_string)
    results, img_width, img_height = get_page_annotations(image_path)
    table = Table(title="Annotations")
    table.add_column("Label", style="cyan")
    table.add_column("Width", justify="right", style="green")
    table.add_column("Height", justify="right", style="green")
    table.add_column("Position", style="yellow")

    # Process results in pairs (bbox and label)
    results = page_annotations["result"]
    for i in range(0, len(results), 2):
        bbox = results[i]
        label_info = results[i + 1]

        width = bbox["value"]["width"]
        height = bbox["value"]["height"]
        x = bbox["value"]["x"]
        y = bbox["value"]["y"]
        label = label_info["value"]["labels"][0]
        table.add_row(label, f"{width:.1f}", f"{height:.1f}", f"({x:.1f}, {y:.1f})")

    rprint(table)

    # Initialize OCR and process image
    from lp_labelstudio.alto_generator import create_alto_xml
    from lp_labelstudio.ocr import ocr_box  # Heavy import: we like it to be inside this function

    # Open the image
    with Image.open(image_path) as img:
        img_width, img_height = img.size
        console = Console()
        all_ocr_results = []

        # Process headlines
        console.print("\n[bold blue]Processing Headlines:[/]")
        for i in range(0, len(results), 2):
            bbox = results[i]
            label_info = results[i + 1]

            if label_info["value"]["labels"][0] == "Headline":
                # Calculate pixel coordinates
                x = int(bbox["value"]["x"] * img_width / 100)
                y = int(bbox["value"]["y"] * img_height / 100)
                width = int(bbox["value"]["width"] * img_width / 100)
                height = int(bbox["value"]["height"] * img_height / 100)

                # Process the box
                box_results = ocr_box(img, (x, y, width, height))

                if box_results:
                    all_ocr_results.extend(box_results)
                    for abs_bbox, (text, confidence) in box_results:
                        console.print(
                            f"[yellow]Position:[/] ({abs_bbox[0]:.1f}, {abs_bbox[1]:.1f})"
                        )
                        console.print(
                            f"[green]Word:[/] {text} [yellow]Confidence:[/] {confidence:.2f}\n"
                        )
                else:
                    console.print(f"[red]No text detected[/] at position ({x}, {y})\n")

        # Generate ALTO XML
        alto_xml = create_alto_xml(img_width, img_height, all_ocr_results)

        # Save ALTO XML
        alto_path = os.path.splitext(image_path)[0] + ".alto.xml"
        with open(alto_path, "w", encoding="utf-8") as f:
            f.write(alto_xml)
        console.print(f"[blue]ALTO XML saved to:[/] {alto_path}")


@cli.command()
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--redo", is_flag=True, help="Reprocess and replace existing annotations")
def process_newspaper(directory: str, redo: bool) -> None:
    """Process newspaper pages (JPEG images) recursively in a directory using layoutparser and convert to Label Studio format."""
    # We import here for performance reasons. Don't move up!
    from lp_labelstudio.image_processing import process_single_image, get_image_size
    from lp_labelstudio.image_processing import convert_to_label_studio_format
    import layoutparser as lp  # type: ignore

    logger.info(f"Processing newspaper pages recursively in directory: {directory}")
    model: lp.models.Detectron2LayoutModel = lp.models.Detectron2LayoutModel(
        NEWSPAPER_MODEL_PATH, label_map=NEWSPAPER_LABEL_MAP
    )

    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith(JPEG_EXTENSION):
                image_path = os.path.join(root, filename)
                output_path = os.path.splitext(image_path)[0] + "_annotations.json"

                if os.path.exists(output_path) and not redo:
                    click.echo(
                        click.style(
                            f"Skipped {image_path} (annotation file exists)",
                            fg="yellow",
                        )
                    )
                    continue

                click.echo(click.style(f"Processing {image_path}...", fg="blue"))

                layout = process_single_image(image_path, model)
                img_width, img_height = get_image_size(image_path)
                label_studio_data = convert_to_label_studio_format(
                    layout, img_width, img_height, filename
                )

                with open(output_path, "w") as f:
                    json.dump(label_studio_data, f, indent=2)
                logger.info(f"Annotations saved to {output_path}")

                summary = generate_summary(image_path, layout, output_path)
                click.echo(summary)

    click.echo(click.style("Processing complete.", fg="green"))


cli.add_command(escriptorium_group)
cli.add_command(labelstudio_api)


@cli.command()
@click.argument(
    "json_files", nargs=-1, type=click.Path(exists=True, file_okay=True, dir_okay=False)
)
def collect_coco(json_files):
    """Collect COCO data from multiple JSON files into a single output file."""
    from lp_labelstudio.collect_coco import collect_coco as cc

    if not json_files:
        click.echo("No JSON files found. Please check your input.")
        return
    cc(json_files)
    click.echo(f"COCO data collected and saved to /tmp/coco-out.json")


@cli.command(name="generate-thumbnails")
@click.argument(
    "source_folder", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.argument("destination_folder", type=click.Path(file_okay=False, dir_okay=True))
def generate_thumbnails_command(source_folder: str, destination_folder: str):
    """Generate thumbnails from images in the source folder and save them in the destination folder."""
    click.echo(f"Generating thumbnails from {source_folder} to {destination_folder}")
    generate_thumbnails(source_folder, destination_folder)
    click.echo("Thumbnail generation complete!")


def get_page_annotations(image_path: Path) -> Tuple[List[Dict], int, int]:
    """
    Get annotations for a page and its dimensions.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple containing:
        - List of annotation results
        - Image width
        - Image height
    """
    manifest_file = image_path.parent / "manifest.json"
    assert manifest_file.exists()
    
    with Image.open(image_path) as img:
        img_width, img_height = img.size
    
    all_pages_annotations = json.load(manifest_file.open())
    current_page = int(image_path.stem.split("_")[1])
    
    page_annotations = [
        annotation["annotations"][0]
        for annotation in all_pages_annotations
        if annotation["data"]["pageNumber"] == current_page
    ][0]
    
    return page_annotations["result"], img_width, img_height


def generate_summary(
    image_path: str, result: List[Dict[str, Any]], output_path: str
) -> str:
    from lp_labelstudio.image_processing import get_image_size

    img_width, img_height = get_image_size(image_path)

    element_counts: Dict[str, int] = {}
    total_chars: int = 0
    for element in result:
        element_type: str = element["type"]
        element_counts[element_type] = element_counts.get(element_type, 0) + 1
        total_chars += len(element.get("text", ""))

    summary = click.style(f"Processed ", fg="green")
    summary += click.style(f"{image_path}", fg="bright_blue")
    summary += click.style(f" ({img_width}x{img_height}): ", fg="green")
    summary += click.style(f"{len(result)}", fg="yellow")
    summary += click.style(" elements detected (", fg="green")
    summary += ", ".join(
        [
            f"{click.style(element_type, fg='cyan')}: {click.style(str(count), fg='yellow')}"
            for element_type, count in element_counts.items()
        ]
    )
    summary += click.style(f"). Total characters: ", fg="green")
    summary += click.style(f"{total_chars}", fg="yellow")
    summary += click.style("). Annotations saved to: ", fg="green")
    summary += click.style(f"{output_path}", fg="bright_blue")
    return summary


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
