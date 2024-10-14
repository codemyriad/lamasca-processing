import click
import os
import json
from typing import List, Dict, Any
from pathlib import Path
from collections import defaultdict

def get_image_url(image_path: str) -> str:
    """Convert local image path to cloud storage URL.

    Example:
    >>> get_image_url("/tmp/newspapers/image.jpg")
    'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/image.jpg'
    """
    return image_path.replace("/tmp/newspapers", "https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers")

def get_page_number(jpeg_file: str) -> int:
    """Extract page number from JPEG filename.

    Example:
    >>> get_page_number("page_01.jpeg")
    1
    """
    return int(jpeg_file.split(".")[0].replace("page_", ""))

def get_date(directory: str) -> str:
    """Extract date from directory name.

    Example:
    >>> get_date("/path/to/lamasca-2023-05-15")
    '2023-05-15'
    """
    return directory.split('/')[-1].replace("lamasca-", "")

@click.argument(
    "directories",
    nargs=-1,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
def generate_labelstudio_manifest(directories: List[str]) -> List[Dict[str, Any]]:
    """Generate Label Studio JSON manifest for the given directories."""
    total_issues: int = 0
    total_pages: int = 0
    total_annotations: int = 0

    all_manifests = []

    for directory in directories:
        manifest: List[Dict[str, Any]] = []
        if directory.endswith('/'):
            directory = directory[:-1]

        publication_name: str = os.path.basename(directory)
        jpeg_files: List[str] = [f for f in os.listdir(directory) if f.lower().endswith('.jpeg')]

        for jpeg_file in jpeg_files:
            image_path: str = os.path.join(directory, jpeg_file)
            image_url: str = get_image_url(image_path)
            page_number: int = get_page_number(jpeg_file)
            date: str = get_date(directory)
            task_item: Dict[str, Any] = {
                "id": get_task_id(directory, jpeg_file),
                "data": {
                    "ocr": image_url,
                    "pageNumber": page_number,
                    "date": date,
                },
            }
            manifest.append(task_item)
        num_annotations = 0
        annotations_path = Path(directory) / "annotations"
        if annotations_path.exists():
            num_annotations = augment_manifest_with_annotations(manifest, directory, annotations_path)
        total_issues += 1
        total_pages += len(manifest)
        total_annotations += num_annotations

        all_manifests.extend(manifest)

        output = Path(directory) / "manifest.json"
        with output.open("w") as f:
            json.dump(manifest, f, indent=2)
        click.echo(click.style(f"Manifest file generated with {num_annotations} annotations: {output}", fg="green"))

    click.echo(click.style(f"Total issues included: {total_issues}", fg="green"))
    click.echo(click.style(f"Total pages included: {total_pages}", fg="green"))
    click.echo(click.style(f"Total annotations included: {total_annotations}", fg="green"))

    return all_manifests

def read_xml_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read()


def augment_manifest_with_annotations(manifest, directory, annotations_path):
    """Finds JSON files for annotations and amends the passed `manifest` dict.
    Returns the number of pages that received annotations
    """
    if not annotations_path.exists():
        return 0
    manifest_by_page = {}
    for page in manifest:
        manifest_by_page[page["data"]["pageNumber"]] = page
    total_annotated = 0
    for contributor_dir in annotations_path.iterdir():
        for file in contributor_dir.iterdir():
            annotation = json.loads(file.read_text())
            annotation.pop("completed_by", None)
            page_number = annotation["task"]["data"]["pageNumber"]
            if not manifest_by_page[page_number].get("annotations"):
                manifest_by_page[page_number]["annotations"] = []
            manifest_by_page[page_number]["annotations"].append(annotation)
            total_annotated += 1
    return total_annotated

def get_task_id(directory_name: str, filename: str) -> str:
    """
    >>> directory_name = "/tmp/newspapers/lamasca-pages/1994/lamasca-1994-01-12"
    >>> filename = "page01.jpeg"
    >>> get_task_id(directory_name, filename)
    '1994-01-12-page01'
    """
    date = directory_name.split('/')[-1]
    return f"{date}-{filename.split('.')[0]}"
