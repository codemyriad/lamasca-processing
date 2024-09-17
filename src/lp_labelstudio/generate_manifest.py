import click
import os
import json
from typing import List, Dict, Any
from pathlib import Path
from PIL import Image

def get_image_url(image_path: str) -> str:
    return image_path.replace("/tmp/newspapers", "https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers")

def get_page_number(jpeg_file: str) -> int:
    return int(jpeg_file.split(".")[0].replace("page_", ""))

def get_date(directory: str) -> str:
    return directory.split('/')[-1].replace("lamasca-", "")

def get_image_info(image_path: str, image_id: int) -> Dict[str, Any]:
    with Image.open(image_path) as img:
        width, height = img.size
    return {
        "id": image_id,
        "file_name": os.path.basename(image_path),
        "width": width,
        "height": height,
        "date_captured": get_date(os.path.dirname(image_path)),
        "license": 1,
        "coco_url": get_image_url(image_path),
        "flickr_url": ""
    }

@click.command()
@click.argument('directories', nargs=-1, type=click.Path(exists=True, file_okay=False, dir_okay=True))
def generate_coco_manifest(directories: List[str]) -> None:
    """Generate COCO 1.0 format JSON manifest files for the given directories,
    and save it in each dir as `coco_manifest.json`."""

    coco_format = {
        "info": {
            "year": 2023,
            "version": "1.0",
            "description": "Archivio del settimanale la masca",
            "contributor": "la masca",
            "url": "http://codemyriad.io",
            "date_created": "2024-10-01"
        },
        "licenses": [
            {
                "id": 1,
                "name": "Attribution-NonCommercial-ShareAlike License",
                "url": "http://creativecommons.org/licenses/by-nc-sa/2.0/"
            }
        ],
        "images": [],
        "annotations": [],
        "categories": [
            {"id": 1, "name": "text", "supercategory": "content"}
        ]
    }

    image_id = 1
    annotation_id = 1

    for directory in directories:
        if directory.endswith('/'):
            directory = directory[:-1]

        jpeg_files = [f for f in os.listdir(directory) if f.lower().endswith('.jpeg')]

        for jpeg_file in jpeg_files:
            image_path = os.path.join(directory, jpeg_file)

            # Add image info
            coco_format["images"].append(get_image_info(image_path, image_id))

            # Add a dummy annotation (since we don't have actual annotations yet)
            coco_format["annotations"].append({
                "id": annotation_id,
                "image_id": image_id,
                "category_id": 1,
                "bbox": [0, 0, 100, 100],  # Dummy bounding box
                "area": 10000,
                "segmentation": [],
                "iscrowd": 0
            })

            image_id += 1
            annotation_id += 1

        output = Path(directory) / "coco_manifest.json"
        with output.open("w") as f:
            json.dump(coco_format, f, indent=2)
        click.echo(click.style(f"COCO manifest file generated: {output}", fg="green"))

    click.echo(click.style(f"Total images included: {image_id - 1}", fg="green"))
    click.echo(click.style(f"Total annotations included: {annotation_id - 1}", fg="green"))

if __name__ == "__main__":
    generate_coco_manifest()
