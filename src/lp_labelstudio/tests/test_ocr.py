import pytest
from rich.console import Console
from rich.table import Table
from rich.text import Text
from collections import defaultdict
from typing import Dict, List
from statistics import mean
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


@pytest.fixture(scope="session")
def test_results():
    results = defaultdict(list)
    yield results
    print_final_summary(results)


def truncate_text(text: str, max_length: int = 80) -> str:
    """Truncate text and make it single line."""
    # Replace newlines with spaces
    text = " ".join(text.split())
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def print_final_summary(test_results: Dict[str, List[dict]]):
    """Print final summary table with statistics for all images."""
    if not test_results:
        return

    # Collect all samples
    all_samples = []
    for page, results in test_results.items():
        for result in results:
            all_samples.append(
                {
                    "image": Path(page).name,
                    "distance": result["distance"],
                    "passed": result["passed"],
                    "text": result["text"],
                    "gt": result["gt"],
                    "url": result["url"]
                }
            )

    # Sort by distance
    all_samples.sort(key=lambda x: x["distance"])

    # Create samples table
    samples_table = Table(show_header=True)
    samples_table.add_column("Distance")
    samples_table.add_column("OCR Text")
    samples_table.add_column("Ground Truth")
    for sample in all_samples:
        # Add URL row (appears as a section header)
        samples_table.add_row(
            f"[blue]{sample['url']}[/blue]",
            "",  # Empty cells for other columns
            "",
            style="bold",
            end_section=True  # Adds a separation after this row
        )
        # Add data row with OCR comparison details
        samples_table.add_row(
            str(sample["distance"]),
            truncate_text(sample["text"]),
            truncate_text(sample["gt"]),
        )

    console.print("\n[bold]Final Summary Across All Images:[/bold]")
    summary_table = Table(show_header=True)
    summary_table.add_column("URL", style="blue")
    summary_table.add_column("Total Tests")
    summary_table.add_column("Perfect", style="green")
    summary_table.add_column("Passed", style="yellow")
    summary_table.add_column("Failed", style="red")
    summary_table.add_column("Perfect Rate")
    summary_table.add_column("Avg Distance")

    total_tests = 0
    total_perfect = 0
    total_passed = 0
    all_distances = []

    for page, results in sorted(test_results.items()):
        n_tests = len(results)
        if n_tests == 0:
            continue

        n_perfect = sum(1 for r in results if r["distance"] == 0)
        n_passed = sum(1 for r in results if r["passed"] and r["distance"] > 0)
        n_failed = n_tests - n_perfect - n_passed
        perfect_rate = f"{(n_perfect/n_tests)*100:.1f}%" if n_tests else "N/A"
        avg_dist = f"{mean(r['distance'] for r in results):.1f}" if results else "N/A"

        total_tests += n_tests
        total_perfect += n_perfect
        total_passed += n_passed
        all_distances.extend(r["distance"] for r in results)

        summary_table.add_row(
            f"file://{(TEST_FILES_ROOT / 'test-results' / Path(page).name).absolute()}",
            str(n_tests),
            str(n_perfect),
            str(n_passed),
            str(n_failed),
            perfect_rate,
            avg_dist,
        )

    # Add totals row
    if total_tests > 0:
        total_perfect_rate = f"{(total_perfect/total_tests)*100:.1f}%"
        total_avg_dist = f"{mean(all_distances):.1f}"
        summary_table.add_row(
            "[bold]file:///TOTAL[/bold]",
            str(total_tests),
            str(total_perfect),
            str(total_passed),
            str(total_tests - total_perfect - total_passed),
            total_perfect_rate,
            total_avg_dist,
            style="bold",
        )

    console.print(summary_table)

    # Print detailed samples table
    console.print("\n[bold]Detailed Samples (sorted by distance):[/bold]")
    samples_table = Table(show_header=True)
    samples_table.add_column("Distance")
    samples_table.add_column("OCR Text")
    samples_table.add_column("Ground Truth")

    console.print("\n[bold]Detailed Samples (sorted by distance):[/bold]")
    console.print(samples_table)


@pytest.mark.parametrize("page", PAGES)
def test_ocr_box(page, test_results):
    page_results = []
    from lp_labelstudio.cli import get_page_annotations

    image_path = TEST_FILES_ROOT / page
    results, img_width, img_height = get_page_annotations(image_path)

    # Prepare output directory
    test_results_dir = TEST_FILES_ROOT / "test-results"
    test_results_dir.mkdir(exist_ok=True)

    with Image.open(image_path) as img:
        total_boxes = len(results) // 2
        for i in range(0, len(results), 2):
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
                        max_distance_threshold = 100  # Practically disabled for now

                        output_filename = (
                            f"{Path(page).stem}_x{x}_y{y}_w{width}_h{height}.png"
                        )
                        output_path = test_results_dir / output_filename
                        file_url = f"file://{output_path.absolute()}"

                        # Store result for summary
                        test_results[page].append(
                            {
                                "text": recognized_text,
                                "gt": gt_entry,
                                "distance": distance,
                                "passed": distance <= max_distance_threshold,
                                "url": file_url,
                            }
                        )

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
