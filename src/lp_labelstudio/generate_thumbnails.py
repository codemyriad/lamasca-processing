import os
import json
from typing import Dict, Any, List
from PIL import Image, ImageDraw
import click

def generate_thumbnails(source_folder: str, destination_folder: str):
    """
    Generate thumbnails from images in the source folder and save them in the destination folder.
    Only process directories with a manifest.json file and annotations in their JSON files.
    """
    for root, dirs, files in os.walk(source_folder):
        if 'manifest.json' not in files:
            continue

        with open(os.path.join(root, 'manifest.json'), 'r') as f:
            manifest = json.load(f)

        for item in manifest:
            image_filename = os.path.basename(item['data']['ocr'])
            annotation_filename = f"{os.path.splitext(image_filename)[0]}_annotations.json"

            if "annotations" not in item:
                continue

            image_path = os.path.join(root, image_filename)
            if not os.path.exists(image_path):
                click.echo(f"Image not found: {image_path}", err=True)
                continue
            process_image(image_path, item["annotations"], source_folder, destination_folder)

def process_image(image_path: str, annotations: List[Dict], source_root: str, destination_folder: str):
    """Process a single image, create a thumbnail with overlays, and save it."""
    with Image.open(image_path) as img:
        # Resize image to 1000 pixels wide
        aspect_ratio = img.height / img.width
        new_size = (1000, int(1000 * aspect_ratio))
        img_resized = img.resize(new_size, Image.LANCZOS)

        # Convert image to RGBA mode
        img_resized = img_resized.convert('RGBA')

        draw = ImageDraw.Draw(img_resized)

        for annotation in annotations:
            for result in annotation['result']:
                if 'labels' in result['value']:
                    label = result['value']['labels'][0]
                    color = get_color_for_label(label)

                    x = result['value']['x'] * new_size[0] / 100
                    y = result['value']['y'] * new_size[1] / 100
                    width = result['value']['width'] * new_size[0] / 100
                    height = result['value']['height'] * new_size[1] / 100

                    draw.rectangle([x, y, x + width, y + height], fill=color + (128,), outline=color)

        # Create the destination directory structure
        rel_path = os.path.relpath(os.path.dirname(image_path), source_root)
        dest_dir = os.path.join(destination_folder, rel_path)
        os.makedirs(dest_dir, exist_ok=True)

        # Convert back to RGB mode and save the thumbnail
        img_rgb = img_resized.convert('RGB')
        thumbnail_path = os.path.join(dest_dir, os.path.basename(image_path))
        img_rgb.save(thumbnail_path)
        click.echo(f"Saved thumbnail: {thumbnail_path}")

def get_color_for_label(label: str) -> tuple:
    """Return a color tuple (R, G, B) for a given label."""
    # You can expand this dictionary with more labels and colors as needed
    color_map = {
        "SubHeadline": (255, 0, 0),  # Red
        "Headline": (0, 255, 0),     # Green
        "BodyText": (0, 0, 255),     # Blue
        # Add more labels and colors here
    }
    return color_map.get(label, (128, 128, 128))  # Default to gray if label not found
