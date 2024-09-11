import click
import os
import json
from typing import List, Dict, Any
from collections import defaultdict

@click.command()
@click.argument('directories', nargs=-1, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('-o', '--output', type=click.Path(file_okay=True, dir_okay=False), required=True, help='Output JSON manifest file')
@click.option('-n', '--max-issues', type=int, default=None, help='Maximum number of issues to include')
def generate_manifest(directories: List[str], output: str, max_issues: int) -> None:
    """Generate a Label Studio JSON manifest file for a project, including newspaper issues with OCR/segmentation."""
    manifest: Dict[str, Any] = {
        "publications": defaultdict(lambda: {"name": "", "pages": []}),
        "ui_xml": read_xml_file(os.path.join(os.path.dirname(__file__), 'ui.xml'))
    }
    total_issues: int = 0

    for directory in directories:
        if directory.endswith('/'):
            directory = directory[:-1]
        if max_issues is not None and total_issues >= max_issues:
            break

        publication_name: str = os.path.basename(directory)
        jpeg_files: List[str] = [f for f in os.listdir(directory) if f.lower().endswith('.jpeg')]

        publication_pages: List[Dict[str, Any]] = []
        for jpeg_file in jpeg_files:
            image_path: str = os.path.join(directory, jpeg_file)
            json_path: str = os.path.splitext(image_path)[0] + '_annotations.json'

            if not os.path.exists(json_path):
                click.echo(click.style(f"Warning: Annotation file not found for {image_path}", fg="yellow"))
                continue

            with open(json_path, 'r') as f:
                annotations: Dict[str, Any] = json.load(f)

            page_item: Dict[str, Any] = {
                "image": os.path.abspath(image_path),
                "annotations": annotations
            }
            publication_pages.append(page_item)

        if publication_pages:
            manifest["publications"][publication_name] = {
                "name": publication_name,
                "pages": publication_pages
            }
            total_issues += 1

    # Convert defaultdict to regular dict for JSON serialization
    manifest["publications"] = dict(manifest["publications"])

    with open(output, 'w') as f:
        json.dump(manifest, f, indent=2)

    click.echo(click.style(f"Manifest file generated: {output}", fg="green"))
    click.echo(click.style(f"Total issues included: {len(manifest['publications'])}", fg="green"))
    click.echo(click.style(f"Total pages included: {sum(len(issue['pages']) for issue in manifest['publications'].values())}", fg="green"))
def read_xml_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read()
