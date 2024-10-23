import os
import json
import numpy as np
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageColor
from .xycut.xycut import recursive_xy_cut
import click
from multiprocessing import Pool, cpu_count
from functools import partial

TRANSPARENCY = 0.25  # Degree of transparency, 0-100%
OPACITY = int(255 * TRANSPARENCY)

def generate_thumbnails(source_folder: str, destination_folder: str):
    """
    Generate thumbnails from images in the source folder and save them in the destination folder.
    Only process directories with a manifest.json file and annotations in their JSON files.

    :param source_folder: Path to the source folder containing images and manifest files
    :param destination_folder: Path to save the generated thumbnails
    :param progress_callback: Optional callback function to report progress
    """
    tasks = []
    for root, dirs, files in os.walk(source_folder):
        if 'manifest.json' not in files:
            continue

        with open(os.path.join(root, 'manifest.json'), 'r') as f:
            manifest = json.load(f)

        for item in manifest:
            image_filename = os.path.basename(item['data']['ocr'])
            image_path = os.path.join(root, image_filename)
            if not os.path.exists(image_path):
                click.echo(f"Image not found: {image_path}", err=True)
                continue
            tasks.append((image_path, item.get("annotations", []), source_folder, destination_folder))

    # Use multiprocessing to process images in parallel
    total_tasks = len(tasks)
    processed_images = 0
    images_with_annotations = 0
    concurrency = int(cpu_count() * 0.8) # Using all CPUs would freeze my laptop
    with Pool(processes=concurrency) as pool:
        with click.progressbar(length=total_tasks, label="Generating thumbnails") as progress_bar:
            for has_annotations in pool.imap_unordered(process_image, tasks):
                processed_images += 1
                if has_annotations:
                    images_with_annotations += 1
                progress_bar.update(1)
                progress_bar.label = f"Processed {processed_images}/{total_tasks} images, {images_with_annotations} with annotations"

def process_image(args):
    """Process a single image, create a thumbnail with overlays, and save it."""
    image_path, annotations, source_root, destination_folder = args
    has_annotations = len(annotations) > 0
    with Image.open(image_path) as img:
        # Resize image to 1000 pixels wide
        aspect_ratio = img.height / img.width
        new_size = (1000, int(1000 * aspect_ratio))
        img_resized = img.resize(new_size, Image.LANCZOS)

        # Convert image to RGBA mode
        img_resized = img_resized.convert('RGBA')

        # Create a blank image for the overlay
        overlay = Image.new('RGBA', img_resized.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Collect all boxes and their metadata
        boxes = []
        box_metadata = []
        for annotation in annotations:
            for result in annotation['result']:
                if 'labels' in result['value']:
                    x = result['value']['x'] * new_size[0] / 100
                    y = result['value']['y'] * new_size[1] / 100
                    width = result['value']['width'] * new_size[0] / 100
                    height = result['value']['height'] * new_size[1] / 100
                    
                    # Skip invalid boxes
                    if width <= 0 or height <= 0:
                        continue
                        
                    boxes.append([x, y, x + width, y + height])
                    box_metadata.append({
                        'label': result['value']['labels'][0],
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height
                    })

        # Sort boxes using recursive XY-cut if we have any valid boxes
        if boxes:
            boxes_array = np.array(boxes)
            sorted_indices = []
            recursive_xy_cut(boxes_array, np.arange(len(boxes)), sorted_indices)
            
            # Draw boxes in sorted order
            for idx, sort_idx in enumerate(sorted_indices):
                meta = box_metadata[sort_idx]
                color = get_color_for_label(meta['label'])
                
                # Draw rectangle
                draw.rectangle([meta['x'], meta['y'], 
                              meta['x'] + meta['width'], 
                              meta['y'] + meta['height']], 
                             fill=color+(OPACITY,))

                # Add index number in the top-left corner of the rectangle
                font_size = max(12, int(min(meta['width'], meta['height']) * 0.2))  # Minimum size of 12px
                from PIL import ImageFont
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()

                index_text = str(idx)  # Use sorted index
                text_bbox = draw.textbbox((meta['x'], meta['y']), index_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                # Draw white background for text
                draw.rectangle([meta['x'], meta['y'], 
                              meta['x'] + text_width + 4, 
                              meta['y'] + text_height + 4],
                             fill=(255, 255, 255, 255))

                # Draw text
                draw.text((meta['x'] + 2, meta['y'] + 2), index_text,
                         fill=(0, 0, 0, 255), font=font)

        # Alpha composite the original image with the overlay
        img_with_overlay = Image.alpha_composite(img_resized, overlay)

        # Create the destination directory structure
        rel_path = os.path.relpath(os.path.dirname(image_path), source_root)
        dest_dir = os.path.join(destination_folder, rel_path)
        os.makedirs(dest_dir, exist_ok=True)

        # Convert back to RGB mode and save the thumbnail
        img_rgb = img_with_overlay.convert('RGB')
        thumbnail_path = os.path.join(dest_dir, os.path.basename(image_path))
        img_rgb.save(thumbnail_path)
        return has_annotations

def get_color_for_label(label: str) -> tuple:
    """Return a color tuple (R, G, B) for a given label."""
    color_map = {
        "Text": "#c8ffbe",
        "Headline": "#d8f1a0",
        "SubHeadline": "#dce593",
        "Author": "#dce593",
        "PageTitle": "#efcb68",
        "PageNumber": "#dcc7be",
        "Date": "#ab7968",
        "Advertisement": "#f46036",
        "Map": "#6d72c3",
        "Photograph": "#a8dadc",
        "Illustration": "#5941a9",
        "Comics/Cartoon": "#e5d4ed",
        "Editorial Cartoon": "#0b4f6c",
    }

    hex_color = color_map.get(label, "#808080")  # Default to gray if label not found
    return ImageColor.getrgb(hex_color)
