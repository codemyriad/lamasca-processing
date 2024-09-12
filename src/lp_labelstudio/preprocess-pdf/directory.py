#!/bin/env python

import click
from pathlib import Path
import logging
from cli import extract_images

@click.command()
@click.argument('input_dir', type=click.Path(exists=True, path_type=Path))
@click.argument('output_dir', type=click.Path(path_type=Path))
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']), default='INFO', help='Set the logging level')
@click.option('--force', is_flag=True, help='Overwrite existing files')
def process_directory(input_dir: Path, output_dir: Path, log_level: str, force: bool=False):
    """
    Process all PDF files in the input directory and extract images to corresponding output directories.

    INPUT_DIR: Path to the directory containing PDF files
    OUTPUT_DIR: Base path for output directories
    """
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    pdf_files = list(input_dir.glob('*.pdf'))
    if not pdf_files:
        logging.warning(f"No PDF files found in {input_dir}")
        return

    for pdf_file in pdf_files:
        pdf_name = pdf_file.stem
        pdf_output_dir = output_dir / pdf_name

        logging.info(f"Processing {pdf_file}")
        extract_images(pdf_file, pdf_output_dir, force)

    logging.info("All PDF files processed.")

if __name__ == '__main__':
    process_directory()
