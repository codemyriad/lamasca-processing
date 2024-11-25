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


@pytest.mark.parametrize("page", PAGES)
def test_ocr_box(page):
    # We need to factor out some functionality from `process_image` to use it here too
