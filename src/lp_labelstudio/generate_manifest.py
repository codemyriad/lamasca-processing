import click
import os
import json
from typing import List, Dict, Any
from pathlib import Path
from collections import defaultdict

@click.command()
@click.argument('directories', nargs=-1, type=click.Path(exists=True, file_okay=False, dir_okay=True))
def generate_manifest(directories: List[str]) -> None:
    """Generate Label Studio JSON manifest files for the given directories,
    and save it in each dir as `manifest.json`."""
    total_issues: int = 0
    total_pages: int = 0

    for directory in directories:
        manifest: List[Dict[str, Any]] = []
        if directory.endswith('/'):
            directory = directory[:-1]

        publication_name: str = os.path.basename(directory)
        jpeg_files: List[str] = [f for f in os.listdir(directory) if f.lower().endswith('.jpeg')]

        for jpeg_file in jpeg_files:
            image_path: str = os.path.join(directory, jpeg_file)
            image_url: str = image_path.replace("/tmp/newspapers", "https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers")
            page_number: int = int(jpeg_file.split(".")[0].replace("page_", ""))
            date = directory.split('/')[-1].replace("lamasca-", "")
            task_item: Dict[str, Any] = {
                "id": get_task_id(directory, jpeg_file),
                "data": {
                    "ocr": image_url,
                    "pageNumber": page_number,
                    "date": date,
                },
            }
            manifest.append(task_item)

        total_issues += 1
        total_pages += len(manifest)

        output = Path(directory) / "manifest.json"
        with output.open("w") as f:
            json.dump(manifest, f, indent=2)
        click.echo(click.style(f"Manifest file generated: {output}", fg="green"))

    click.echo(click.style(f"Total issues included: {total_issues}", fg="green"))
    click.echo(click.style(f"Total pages included: {total_pages}", fg="green"))

def read_xml_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read()


def get_task_id(directory_name: str, filename: str) -> str:
    """
    >>> directory_name = "/tmp/newspapers/lamasca-pages/1994/lamasca-1994-01-12"
    >>> filename = "page01.jpeg"
    >>> get_task_id(directory_name, filename)
    '1994-01-12-page01'
    """
    date = directory_name.split('/')[-1]
    return f"{date}-{filename.split('.')[0]}"
