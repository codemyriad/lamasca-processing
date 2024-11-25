import pytest
from lp_labelstudio.cli import process_image
from lp_labelstudio.tests.setup_test import prepare, PAGES, TEST_FILES_ROOT
from PIL import Image
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
    
    with Image.open(image_path) as img:
        # Test OCR on headlines
        for i in range(0, len(results), 2):
            bbox = results[i]
            label_info = results[i + 1]
            
            if label_info["value"]["labels"][0] == "Headline":
                # Calculate pixel coordinates
                x = int(bbox["value"]["x"] * img_width / 100)
                y = int(bbox["value"]["y"] * img_height / 100)
                width = int(bbox["value"]["width"] * img_width / 100)
                height = int(bbox["value"]["height"] * img_height / 100)
                
                # Process the box
                box_results = ocr_box(img, (x, y, width, height))
                
                # Basic assertions
                assert box_results is not None, f"OCR should return results for headline at ({x}, {y})"
                assert len(box_results) > 0, f"OCR should detect at least one word in headline at ({x}, {y})"
                
                # Check structure of results
                for abs_bbox, (text, confidence) in box_results:
                    assert len(abs_bbox) == 4, "Bounding box should have 4 coordinates"
                    assert isinstance(text, str), "OCR text should be string"
                    assert isinstance(confidence, float), "Confidence should be float"
                    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
