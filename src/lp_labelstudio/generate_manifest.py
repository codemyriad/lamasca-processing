import click
import os
import json
import zipfile
from typing import List, Dict, Any
from pathlib import Path
from PIL import Image


def get_image_url(image_path: str) -> str:
    return image_path.replace(
        "/tmp/newspapers",
        "https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers",
    )


def get_page_number(jpeg_file: str) -> int:
    return int(jpeg_file.split(".")[0].replace("page_", ""))


def get_date(directory: str) -> str:
    return directory.split("/")[-1].replace("lamasca-", "")


def get_image_info(image_path: str) -> Dict[str, Any]:
    with Image.open(image_path) as img:
        width, height = img.size
    return {
        "file_name": os.path.basename(image_path),
        "height": height,
        "width": width,
        "url": get_image_url(image_path),
    }


@click.command()
@click.argument(
    "directories",
    nargs=-1,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
def generate_datumaro_manifest(directories: List[str]) -> None:
    """Generate Datumaro format ZIP file containing JSON manifest for the given directories."""

    for directory in directories:
        if directory.endswith("/"):
            directory = directory[:-1]

        datumaro_format = {
            "info": {},
            "categories": {
                "label": {
                    "labels": [
                        {"name": "newspaper_page", "parent": "", "attributes": []}
                    ],
                    "attributes": [],
                }
            },
            "items": [],
        }

        jpeg_files = [f for f in os.listdir(directory) if f.lower().endswith(".jpeg")]

        for jpeg_file in jpeg_files:
            image_path = os.path.join(directory, jpeg_file)
            item_id = os.path.splitext(jpeg_file)[0]

            datumaro_format["items"].append(
                {"id": item_id, "annotations": [], "image": get_image_info(image_path)}
            )

        output = os.path.join(directory, "datumaro.zip")
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(
                "annotations/default.json", json.dumps(datumaro_format, indent=2)
            )

        click.echo(click.style(f"Datumaro ZIP file generated: {output}", fg="green"))
        click.echo(
            click.style(
                f"Total images included: {len(datumaro_format['items'])}", fg="green"
            )
        )


if __name__ == "__main__":
    generate_datumaro_manifest()
