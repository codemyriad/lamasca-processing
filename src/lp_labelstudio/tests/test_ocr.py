import pytest
from lp_labelstudio.cli import process_image
from lp_labelstudio.tests.setup_test import prepare, PAGES, TEST_FILES_ROOT
from PIL import Image, ImageDraw
import numpy as np
from lp_labelstudio.ocr import ocr_box


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
                    # Draw OCR detected rectangle
                    draw.rectangle(
                        [coords[0], coords[1], coords[2], coords[3]], 
                        outline='red', 
                        width=2
                    )
                    # Draw text with confidence
                    draw.text(
                        (coords[0], coords[1] - 20),
                        f"{text} ({confidence:.2f})",
                        fill='red'
                    )
        
        # Save the annotated image with all boxes
        output_path = test_results_dir / f"ocr_overlay_{Path(page).stem}.png"
        img_draw.save(output_path)
