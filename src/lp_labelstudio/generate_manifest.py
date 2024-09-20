import click
import os
import json
from typing import List, Dict, Any
from pathlib import Path
from PIL import Image


def get_image_url(image_path: str) -> str:
    # Ensure the URL uses HTTPS and is properly formatted
    return f"https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/{'/'.join(image_path.split('/')[3:])}"


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
def generate_iiif_manifest(directories: List[str]) -> None:
    """Generate IIIF manifest JSON file for the given directories."""

    for directory in directories:
        if directory.endswith("/"):
            directory = directory[:-1]

        newspaper_name = os.path.basename(directory).split('-')[0]
        publication_date = get_date(directory)

        iiif_manifest = {
            "@context": "http://iiif.io/api/presentation/3/context.json",
            "id": f"https://example.org/iiif/newspaper/{os.path.basename(directory)}/manifest",
            "type": "Manifest",
            "label": {"en": [f"Newspaper: {newspaper_name}"]},
            "behavior": ["paged"],
            "metadata": [
                {"label": {"en": ["Publication"]}, "value": {"en": [newspaper_name]}},
                {"label": {"en": ["Date"]}, "value": {"en": [publication_date]}},
            ],
            "items": [],
        }

        jpeg_files = sorted([f for f in os.listdir(directory) if f.lower().endswith(".jpeg")])

        for i, jpeg_file in enumerate(jpeg_files):
            image_path = os.path.join(directory, jpeg_file)
            image_info = get_image_info(image_path)
            
            canvas = {
                "id": f"https://example.org/iiif/newspaper/{os.path.basename(directory)}/canvas/p{i+1}",
                "type": "Canvas",
                "label": {"en": [f"Page {i+1}"]},
                "height": image_info["height"],
                "width": image_info["width"],
                "items": [
                    {
                        "id": f"https://example.org/iiif/newspaper/{os.path.basename(directory)}/page/p{i+1}/1",
                        "type": "AnnotationPage",
                        "items": [
                            {
                                "id": f"https://example.org/iiif/newspaper/{os.path.basename(directory)}/annotation/p{i+1}-image",
                                "type": "Annotation",
                                "motivation": "painting",
                                "body": {
                                    "id": image_info["url"],
                                    "type": "Image",
                                    "format": "image/jpeg",
                                    "height": image_info["height"],
                                    "width": image_info["width"],
                                    "service": [
                                        {
                                            "@id": image_info["url"],
                                            "type": "ImageService3",
                                            "profile": "level1"
                                        }
                                    ]
                                },
                                "target": f"https://example.org/iiif/newspaper/{os.path.basename(directory)}/canvas/p{i+1}"
                            }
                        ]
                    }
                ]
            }
            iiif_manifest["items"].append(canvas)

        output = os.path.join(directory, "manifest.json")
        with open(output, "w") as f:
            json.dump(iiif_manifest, f, indent=2)

        click.echo(click.style(f"IIIF manifest generated: {output}", fg="green"))
        click.echo(
            click.style(
                f"Total images included: {len(iiif_manifest['items'])}", fg="green"
            )
        )


if __name__ == "__main__":
    generate_iiif_manifest()
