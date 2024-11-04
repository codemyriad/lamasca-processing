import os
import json
import numpy as np
from typing import Dict, Any, List, Tuple
from .article_reconstruction import ArticleReconstructor
from PIL import Image, ImageDraw, ImageFont, ImageColor
from .xycut.text_sorting import sort_text_areas
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
    
    def draw_debug_info(draw, zone, x, y, debug_info):
        """Helper to draw debug information for a zone"""
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        
        # Just show the label
        debug_text = [zone.label]
        
        if zone.debug_weights:
            for key, value in zone.debug_weights.items():
                debug_text.append(f"{key}: {value}")
        
        # White background for better readability
        text_height = len(debug_text) * 15
        text_width = max(len(text) * 7 for text in debug_text)  # Approximate width
        draw.rectangle([x, y-text_height-5, x+text_width, y-5], 
                      fill=(255, 255, 255, 200))
        
        # Draw each line of debug text
        for i, line in enumerate(debug_text):
            draw.text((x, y-text_height+(i*15)), line,
                     fill=(0, 0, 0, 255), font=font)
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
                        
                    boxes.append([int(x), int(y), int(x + width), int(y + height)])
                    box_metadata.append({
                        'label': result['value']['labels'][0],
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height
                    })

        # Use article reconstruction to group and color boxes
        if boxes:
            # Initialize article reconstructor
            reconstructor = ArticleReconstructor()
            
            # Add zones from annotations
            for result in annotation['result']:
                if 'labels' in result['value']:
                    reconstructor.add_zone(result)
            
            # Build connectivity graph and reconstruct articles
            reconstructor.build_graph()
            articles = reconstructor.reconstruct_articles()
            
            # Draw connectivity graph first
            for zone1_id, connections in reconstructor.graph.items():
                zone1 = next(z for z in reconstructor.zones if z.id == zone1_id)
                start_x = zone1.x * new_size[0] / 100
                start_y = zone1.y * new_size[1] / 100
            
                for connected_id, weight in connections:
                    zone2 = next(z for z in reconstructor.zones if z.id == connected_id)
                    end_x = zone2.x * new_size[0] / 100
                    end_y = zone2.y * new_size[1] / 100
                
                    # Draw connection line with opacity based on weight
                    line_opacity = int(255 * min(weight, 1.0))
                    draw.line([(start_x, start_y), (end_x, end_y)],
                             fill=(255, 0, 0, line_opacity), width=2)

            # Draw boxes colored by article grouping
            for article_idx, article in enumerate(articles):
                # Use different hue for each article
                hue = (article_idx * 137.5) % 360  # Golden angle to spread colors
                for zone in article:
                    # Convert coordinates to thumbnail scale
                    x = zone.x * new_size[0] / 100
                    y = zone.y * new_size[1] / 100
                    width = zone.width * new_size[0] / 100
                    height = zone.height * new_size[1] / 100
                
                    # Draw rectangle with article-specific color
                    color = get_color_for_label(zone.label)
                    draw.rectangle([x, y, x + width, y + height],
                                 fill=color+(OPACITY,))
                
                    # Draw debug info above each zone
                    draw_debug_info(draw, zone, x, y, zone.debug_weights)
                
                    # Draw article number in the first zone of each article
                    if zone == article[0]:
                        # Draw white background for number
                        number_size = max(int(height/2), 20)  # Minimum size of 20px
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", number_size)
                        number_text = str(article_idx + 1)
                        text_bbox = draw.textbbox((0, 0), number_text, font=font)
                        text_width = text_bbox[2] - text_bbox[0]
                        text_height = text_bbox[3] - text_bbox[1]
                    
                        # Draw white background rectangle
                        padding = 4
                        draw.rectangle([x, y, 
                                      x + text_width + 2*padding,
                                      y + text_height + 2*padding],
                                     fill=(255, 255, 255, 255))
                    
                        # Draw black text
                        draw.text((x + padding, y + padding),
                                number_text,
                                fill=(0, 0, 0, 255),
                                font=font)

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
