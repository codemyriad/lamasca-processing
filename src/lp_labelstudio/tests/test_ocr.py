import pytest
from lp_labelstudio.cli import process_image
from lp_labelstudio.tests.setup_test import prepare, PAGES, TEST_FILES_ROOT
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from lp_labelstudio.ocr import ocr_box


def get_font(size=36):
    """Get a font with fallback options."""
    try:
        # Try different font paths
        font_paths = [
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf",
            "/System/Library/Fonts/Helvetica.ttf"
        ]
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except OSError:
                continue
        # If no fonts found, use default
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


@pytest.fixture(autouse=True)
def setup():
    prepare()


@pytest.mark.parametrize("page", PAGES)
def test_process_image(page):
    process_image.callback(TEST_FILES_ROOT / page, redo=True)


import json
from pathlib import Path
from PIL import Image


@pytest.mark.parametrize("page", PAGES)
def test_ocr_box(page):
    from lp_labelstudio.cli import get_page_annotations

    image_path = TEST_FILES_ROOT / page
    results, img_width, img_height = get_page_annotations(image_path)
    
    # Prepare output directory
    test_results_dir = TEST_FILES_ROOT / 'test-results'
    test_results_dir.mkdir(exist_ok=True)

    with Image.open(image_path) as img:
        # Create a single copy of the image for drawing all boxes
        img_draw = img.copy()
        draw = ImageDraw.Draw(img_draw)
        
        # Test OCR on headlines
        for i in range(0, len(results), 2):
            bbox = results[i]
            label_info = results[i + 1]

            if label_info["value"]["labels"][0] in ["Headline", "SubHeadline"]:
                # Calculate pixel coordinates
                x = int(bbox["value"]["x"] * img_width / 100)
                y = int(bbox["value"]["y"] * img_height / 100)
                width = int(bbox["value"]["width"] * img_width / 100)
                height = int(bbox["value"]["height"] * img_height / 100)

                # Process the box
                box_results = ocr_box(img, (x, y, width, height))
                # box_results looks like this:
                # [([1471, 933, 3195, 988], ('l medico Jgo Sturleseil portabandiera dei pro', 0.9333662986755371)),
                #  ([1471, 933, 3195, 988], ('essisti alla Camero', 0.8172330260276794))]

                # Basic assertions
                assert (
                    box_results is not None
                ), f"OCR should return results for headline at ({x}, {y})"

                # Draw original bounding box
                draw.rectangle(
                    [x, y, x + width, y + height],
                    outline='blue',
                    width=2
                )
                
                # Draw OCR results
                for coords, (text, confidence) in box_results:
                    # Draw OCR detected rectangle with thicker border
                    draw.rectangle(
                        [coords[0], coords[1], coords[2], coords[3]], 
                        outline='red', 
                        width=4
                    )
                    # Use consistent font size
                    font = get_font(24)
                    
                    # Split text into lines of max 50 chars
                    text_with_conf = f"{text} ({confidence:.2f})"
                    lines = [text_with_conf[i:i+50] for i in range(0, len(text_with_conf), 50)]
                    
                    # Calculate text background
                    padding = 4
                    # Get text dimensions using getbbox() instead of deprecated getsize()
                    def get_text_size(text):
                        bbox = font.getbbox(text)
                        return bbox[2] - bbox[0], bbox[3] - bbox[1]
                            
                    line_height = get_text_size('A')[1] + padding
                    max_width = max(get_text_size(line)[0] for line in lines)
                    # Position text above the box with more padding
                    text_top = coords[1] - (line_height * len(lines)) - padding * 2
                    bg_bbox = [
                        coords[0], 
                        text_top,
                        coords[0] + max_width + padding*2,
                        text_top + (line_height * len(lines)) + padding
                    ]
                    
                    # Draw semi-transparent background
                    overlay = Image.new('RGBA', img_draw.size, (0,0,0,0))
                    overlay_draw = ImageDraw.Draw(overlay)
                    overlay_draw.rectangle(bg_bbox, fill=(255,255,255,180))
                    img_draw = Image.alpha_composite(img_draw.convert('RGBA'), overlay)
                    draw = ImageDraw.Draw(img_draw)
                    
                    # Draw each line of text
                    for i, line in enumerate(lines):
                        y_pos = text_top + (i * line_height)
                        draw.text(
                            (coords[0] + padding, y_pos),
                            line,
                            fill='red',
                            font=font
                        )
        
        # Save the annotated image with all boxes
        output_path = test_results_dir / f"ocr_overlay_{Path(page).stem}.png"
        img_draw.save(output_path)
