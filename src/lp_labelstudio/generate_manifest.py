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
            "@context": "http://iiif.io/api/presentation/2/context.json",
            "@id": f"https://example.org/iiif/newspaper/{os.path.basename(directory)}/manifest.json",
            "@type": "sc:Manifest",
            "label": f"Newspaper: {newspaper_name}",
            "metadata": [
                {"label": "Publication", "value": newspaper_name},
                {"label": "Date", "value": publication_date},
            ],
            "description": f"IIIF manifest for {newspaper_name} published on {publication_date}",
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "attribution": "Provided by Example Organization",
            "sequences": [
                {
                    "@id": f"https://example.org/iiif/newspaper/{os.path.basename(directory)}/sequence/normal",
                    "@type": "sc:Sequence",
                    "canvases": []
                }
            ]
        }

        jpeg_files = sorted([f for f in os.listdir(directory) if f.lower().endswith(".jpeg")])

        for i, jpeg_file in enumerate(jpeg_files):
            image_path = os.path.join(directory, jpeg_file)
            image_info = get_image_info(image_path)
            
            canvas = {
                "@id": f"https://example.org/iiif/newspaper/{os.path.basename(directory)}/canvas/p{i+1}",
                "@type": "sc:Canvas",
                "label": f"Page {i+1}",
                "height": image_info["height"],
                "width": image_info["width"],
                "images": [
                    {
                        "@type": "oa:Annotation",
                        "motivation": "sc:painting",
                        "resource": {
                            "@id": image_info["url"],
                            "@type": "dctypes:Image",
                            "format": "image/jpeg",
                            "height": image_info["height"],
                            "width": image_info["width"],
                            "service": {
                                "@context": "http://iiif.io/api/image/2/context.json",
                                "@id": image_info["url"],
                                "profile": "http://iiif.io/api/image/2/level1.json"
                            }
                        },
                        "on": f"https://example.org/iiif/newspaper/{os.path.basename(directory)}/canvas/p{i+1}"
                    }
                ],
                "thumbnail": {
                    "@id": f"{image_info['url']}/full/200,/0/default.jpg",
                    "@type": "dctypes:Image",
                    "format": "image/jpeg",
                    "height": 200,
                    "width": int(200 * (image_info["width"] / image_info["height"]))
                }
            }
            iiif_manifest["sequences"][0]["canvases"].append(canvas)

        # Add thumbnail for the manifest
        if jpeg_files:
            first_image = get_image_info(os.path.join(directory, jpeg_files[0]))
            iiif_manifest["thumbnail"] = {
                "@id": f"{first_image['url']}/full/200,/0/default.jpg",
                "@type": "dctypes:Image",
                "format": "image/jpeg",
                "height": 200,
                "width": int(200 * (first_image["width"] / first_image["height"]))
            }

        output = os.path.join(directory, "manifest.json")
        with open(output, "w") as f:
            json.dump(iiif_manifest, f, indent=2)

        click.echo(click.style(f"IIIF manifest generated: {output}", fg="green"))
        click.echo(
            click.style(
                f"Total images included: {len(iiif_manifest['sequences'][0]['canvases'])}", fg="green"
            )
        )


if __name__ == "__main__":
    generate_iiif_manifest()
