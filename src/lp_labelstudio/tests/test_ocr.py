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
        for i in range(0, len(results), 2):
            bbox = results[i]
            label_info = results[i + 1]

            if label_info["value"]["labels"][0] in ["Headline", "SubHeadline"]:
                x = int(bbox["value"]["x"] * img_width / 100)
                y = int(bbox["value"]["y"] * img_height / 100)
                width = int(bbox["value"]["width"] * img_width / 100)
                height = int(bbox["value"]["height"] * img_height / 100)

                box_results = ocr_box(img, (x, y, width, height))
                assert box_results is not None, f"OCR should return results for headline at ({x}, {y})"

                cropped_img = img.crop((x, y, x + width, y + height))
                new_height = height * 2
                new_img = Image.new('RGB', (width, new_height), color='white')
                new_img.paste(cropped_img, (0, 0))

                recognized_text = "\n".join([text for coords, (text, confidence) in box_results])
                draw = ImageDraw.Draw(new_img)
                font = get_font(size=24)
                text_start_y = height + 10

                draw.text(
                    (10, text_start_y),
                    recognized_text,
                    fill='black',
                    font=font
                )

                output_filename = f"{Path(page).stem}_x{x}_y{y}_w{width}_h{height}.png"
                output_path = test_results_dir / output_filename
                new_img.save(output_path)
