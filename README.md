# LP-LabelStudio

## Important Note for Detectron2 Users

To make this project work correctly, you need to modify the `detection_checkpoint.py` file in the Detectron2 library. This modification is necessary to solve a problem with Dropbox URLs.

Add the following line in the `detection_checkpoint.py` file:

```python
queries.pop("dl", None) # Added by Silvio to solve problem with dropbox urls
```

This line should be added in the appropriate location within the file, typically where URL queries are being processed.

## Usage

You can use LP-LabelStudio in two ways:

1. As a module:

```bash
python -m lp_labelstudio [COMMAND] [ARGS]
```

2. Directly using the CLI script:

```bash
python src/lp_labelstudio/cli.py [COMMAND] [ARGS]
```

Available commands:

- `hello`: Simple command that says hello.
- `process-dir`: Process a directory of images.
- `process-image`: Process a single PNG image using layoutparser.
- `process-newspaper`: Process newspaper pages (PNG images) in a directory, including OCR.

For example, to process newspaper pages, generate Label Studio annotations, and perform OCR:

```bash
python -m lp_labelstudio process-newspaper /tmp/newspapers/lamasca-pages/1994/lamasca-1994-01-19/
```

or

```bash
python src/lp_labelstudio/cli.py process-newspaper /tmp/newspapers/lamasca-pages/1994/lamasca-1994-01-19/
```

These commands will process all PNG images in the specified directory, treating them as newspaper pages. They will generate annotation JSON files next to each image, including OCR results for each detected block.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/lp-labelstudio.git
   cd lp-labelstudio
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```

3. Install the dependencies:
   ```bash
   pip install layoutparser paddleocr click Pillow opencv-python numpy
   ```

   Note: If you encounter issues installing PaddleOCR, you may need to install it separately:
   ```bash
   pip install "paddleocr>=2.0.1"
   ```

### Dependencies

This project requires the following main dependencies:

- layoutparser
- PaddleOCR
- click
- Pillow
- opencv-python
- numpy

These will be installed automatically when you follow the installation steps above.

## Contributing

[Add contribution guidelines here]

## License

[Add license information here]
