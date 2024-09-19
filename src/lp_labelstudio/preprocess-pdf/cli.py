#!/bin/env python

import click
from pathlib import Path
import pymupdf
import sys
from PIL import Image
import io
import logging
import numpy as np
from jdeskew.estimator import get_angle
from jdeskew.utility import rotate


def extract_images(input_pdf: Path, output_dir: Path, force: bool = False):
    """
    Extract images from a PDF file, rotate them 180 degrees, deskew, and save them in grayscale.

    input_pdf: Path to the input PDF file
    output_dir: Directory to save the output images
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc = pymupdf.open(input_pdf)
    except Exception as e:
        logging.error(f"Failed to open PDF file: {input_pdf}. Error: {e}")
        return

    for page_num, page in enumerate(doc, start=1):
        image_list = page.get_images()

        if len(image_list) != 1:
            raise ValueError(
                f"Page {page_num:02d} has {len(image_list)} images. Expected 1 image per page."
            )

        for img_index, img in enumerate(image_list, start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)

            output_path = output_dir / f'page_{page_num:02d}.{base_image["ext"]}'

            if not force and output_path.exists():
                logging.info(
                    f"Skipping page {page_num:02d}, file already exists: {output_path}"
                )
                continue
            image_bytes = base_image.pop("image")

            img = Image.open(io.BytesIO(image_bytes))
            if page.rotation:
                img = img.rotate(page.rotation)
            img = img.convert("L")

            # Deskew
            img_array = np.array(img)
            angle = get_angle(img_array)
            img_array = rotate(img_array, angle)
            img = Image.fromarray(img_array)

            img.save(output_path)

            logging.info(
                f"Extracted, processed, and deskewed page {page_num:02d} as {output_path} (skew angle: {angle:.2f} degrees)"
            )

    doc.close()
    logging.info(
        f"PDF image extraction, rotation, deskewing, and grayscale conversion completed."
    )


@click.command()
@click.argument("input_pdf", type=click.Path(exists=True, path_type=Path))
@click.argument("output_dir", type=click.Path(path_type=Path))
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Set the logging level",
)
@click.option("--force", is_flag=True, help="Overwrite existing files")
def cli_extract_images(
    input_pdf: Path, output_dir: Path, log_level: str, force: bool = False
):
    """
    Command-line interface for extracting images from a PDF file.

    INPUT_PDF: Path to the input PDF file
    OUTPUT_DIR: Directory to save the output images
    """
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    extract_images(input_pdf, output_dir, force)


if __name__ == "__main__":
    cli_extract_images()
