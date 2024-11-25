import pytest
from rich.console import Console
from rich.progress import track
from rich.panel import Panel
from rich.table import Table
import pytest
from lp_labelstudio.cli import process_image
from lp_labelstudio.tests.setup_test import prepare, PAGES, TEST_FILES_ROOT
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from lp_labelstudio.ocr import ocr_box
import Levenshtein
from lp_labelstudio.tests.ocr_ground_truth import ground_truth_data

from ppocr.utils.logging import get_logger
import logging


logger = get_logger()
logger.setLevel(logging.ERROR)

console = Console()


def get_font(size=36):
    """Get a font with fallback options."""
    try:
        # Try different font paths
        font_paths = [
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf",
            "/System/Library/Fonts/Helvetica.ttf",
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
    test_results_dir = TEST_FILES_ROOT / "test-results"
    test_results_dir.mkdir(exist_ok=True)

    with Image.open(image_path) as img:
        total_boxes = len(results) // 2
        for i in track(
            range(0, len(results), 2),
            description=f"Processing {page}",
            total=total_boxes,
        ):
            bbox = results[i]
            label_info = results[i + 1]

            if label_info["value"]["labels"][0] in ["Headline", "SubHeadline"]:
                x = int(bbox["value"]["x"] * img_width / 100)
                y = int(bbox["value"]["y"] * img_height / 100)
                width = int(bbox["value"]["width"] * img_width / 100)
                height = int(bbox["value"]["height"] * img_height / 100)

                box_results = ocr_box(img, (x, y, width, height))
                assert (
                    box_results is not None
                ), f"OCR should return results for headline at ({x}, {y})"

                recognized_text = "\n".join(
                    [text for coords, (text, confidence) in box_results]
                )

                # Create identifier for this box
                image_name = Path(page).name
                box_id = f"{x}_{y}_{width}_{height}"

                # Initialize or update ground truth data structure
                if image_name not in ground_truth_data:
                    ground_truth_data[image_name] = {}

                if box_id not in ground_truth_data[image_name]:
                    ground_truth_data[image_name][box_id] = {
                        "ocr": recognized_text,
                        "ground_truth": f"# {recognized_text}",  # Commented out by default
                    }

                # Save the updated ground truth data
                with open(
                    Path(__file__).parent / "ocr_ground_truth.py", "w", encoding="utf-8"
                ) as f:
                    f.write('"""\nGround truth data for OCR testing.\n\n')
                    f.write("Format:\n")
                    f.write('{\n    "image_name": {\n        "x_y_width_height": {\n')
                    f.write('            "ocr": "text from OCR",\n')
                    f.write(
                        '            "ground_truth": "# correct text after manual verification"\n'
                    )
                    f.write("        }\n    }\n}\n\n")
                    f.write(
                        'Uncomment the ground_truth lines as you verify them.\n"""\n\n'
                    )
                    f.write(f"ground_truth_data = {repr(ground_truth_data)}\n")

                # Check if this box has verified ground truth (uncommented)
                if (
                    image_name in ground_truth_data
                    and box_id in ground_truth_data[image_name]
                ):
                    gt_entry = ground_truth_data[image_name][box_id]["ground_truth"]
                    if not gt_entry.startswith(
                        "#"
                    ):  # Only test if ground truth is uncommented
                        distance = Levenshtein.distance(recognized_text, gt_entry)
                        max_distance_threshold = 10

                        table = Table(
                            title=f"OCR Test Results for {image_name} box {box_id}"
                        )
                        table.add_column("Type", style="cyan")
                        table.add_column("Text", style="white")
                        table.add_row("OCR text", recognized_text)
                        table.add_row("Ground truth", gt_entry)
                        table.add_row("Levenshtein distance", str(distance))

                        style = "green" if distance <= max_distance_threshold else "red"
                        console.print(Panel(table, style=style))

                        assert distance <= max_distance_threshold, (
                            f"OCR result differs from ground truth by {distance} characters, "
                            f"which is more than the allowed threshold of {max_distance_threshold}."
                        )

                # Create visualization
                cropped_img = img.crop((x, y, x + width, y + height))
                new_height = height * 2
                new_img = Image.new("RGB", (width, new_height), color="white")
                new_img.paste(cropped_img, (0, 0))
                draw = ImageDraw.Draw(new_img)
                font = get_font(size=24)
                text_start_y = height + 10

                draw.text((10, text_start_y), recognized_text, fill="black", font=font)

                output_filename = f"{Path(page).stem}_x{x}_y{y}_w{width}_h{height}.png"
                output_path = test_results_dir / output_filename
                new_img.save(output_path)
