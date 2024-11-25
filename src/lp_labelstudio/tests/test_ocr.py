import pytest
from PIL import Image
import numpy as np
from lp_labelstudio.ocr import ocr_box

def test_ocr_box():
    # Create a test image with text
    img = Image.new('RGB', (200, 50), color='white')
    # You would need to add some text to the image here
    # This is just a skeleton test
    
    # Define a box that covers the whole image
    box = (0, 0, 200, 50)
    
    # Run OCR
    results = ocr_box(img, box)
    
    # Basic structure tests
    assert isinstance(results, list)
    if results:  # If text was detected
        result = results[0]
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)  # bbox coordinates
        assert isinstance(result[1], tuple)  # (text, confidence)
        assert len(result[1]) == 2
        assert isinstance(result[1][0], str)  # text
        assert isinstance(result[1][1], float)  # confidence
