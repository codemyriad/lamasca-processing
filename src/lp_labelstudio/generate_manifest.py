import click
import os
import json
from typing import List, Dict, Any
import random

@click.command()
@click.argument('directories', nargs=-1, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('-o', '--output', type=click.Path(file_okay=True, dir_okay=False), required=True, help='Output JSON manifest file')
@click.option('-n', '--max-images', type=int, default=None, help='Maximum number of images to include')
def generate_manifest(directories: List[str], output: str, max_images: int) -> None:
    """Generate a Label Studio JSON manifest file for a project, including newspaper issues with OCR/segmentation."""
    manifest: List[Dict[str, Any]] = []
    total_images: int = 0

    for directory in directories:
        issue_name: str = os.path.basename(directory)
        jpeg_files: List[str] = [f for f in os.listdir(directory) if f.lower().endswith('.jpeg')]
        
        for jpeg_file in jpeg_files:
            if max_images is not None and total_images >= max_images:
                break

            image_path: str = os.path.join(directory, jpeg_file)
            json_path: str = os.path.splitext(image_path)[0] + '_annotations.json'

            if not os.path.exists(json_path):
                click.echo(click.style(f"Warning: Annotation file not found for {image_path}", fg="yellow"))
                continue

            with open(json_path, 'r') as f:
                annotations: Dict[str, Any] = json.load(f)

            manifest_item: Dict[str, Any] = {
                "image": os.path.abspath(image_path),
                "issue": issue_name,
                "annotations": annotations
            }
            manifest.append(manifest_item)
            total_images += 1

        if max_images is not None and total_images >= max_images:
            break

    # Shuffle the manifest to ensure a random selection if max_images is less than total available
    random.shuffle(manifest)
    if max_images is not None:
        manifest = manifest[:max_images]

    with open(output, 'w') as f:
        json.dump(manifest, f, indent=2)

    click.echo(click.style(f"Manifest file generated: {output}", fg="green"))
    click.echo(click.style(f"Total images included: {len(manifest)}", fg="green"))
