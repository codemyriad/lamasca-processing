# LP-LabelStudio

## Important Note for Detectron2 Users

To make this project work correctly, you need to modify the `detection_checkpoint.py` file in the Detectron2 library. This modification is necessary to solve a problem with Dropbox URLs.

Add the following line in the `detection_checkpoint.py` file:

```python
queries.pop("dl", None) # Added by Silvio to solve problem with dropbox urls
```

This line should be added in the appropriate location within the file, typically where URL queries are being processed.

## Installation

1. Install system dependencies (optional, for full functionality including PDF support):
   - On Ubuntu/Debian:
     ```bash
     sudo apt-get update
     sudo apt-get install -y libmupdf-dev
     ```
   - On macOS (using Homebrew):
     ```bash
     brew install mupdf
     ```

2. Clone the repository:
   ```bash
   git clone https://github.com/your-username/lp-labelstudio.git
   cd lp-labelstudio
   ```

3. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```

4. Install the package in editable mode:
   ```bash
   pip install -e .
   ```

This will install all the required dependencies automatically.

## Usage

After installation, you can use LP-LabelStudio as a command-line tool:

```bash
lp-labelstudio [COMMAND] [ARGS]
```

Available commands:

- `hello`: Simple command that says hello.
- `process-dir`: Process a directory of images.
- `process-image`: Process a single PNG image using layoutparser.
- `process-newspaper`: Process newspaper pages (PNG images) in a directory, including OCR.

For example, to process newspaper pages, generate Label Studio annotations, and perform OCR:

```bash
lp-labelstudio process-newspaper /tmp/newspapers/lamasca-pages/1994/lamasca-1994-01-19/
```

This command will process all PNG images in the specified directory, treating them as newspaper pages. It will generate annotation JSON files next to each image, including OCR results for each detected block.

## Note

If you encounter issues with PyMuPDF installation, you can still use the core functionality of this project. PyMuPDF is only required for processing PDF files. If you don't need PDF support, you can ignore any PyMuPDF-related errors during installation.

## Contributing

[Add contribution guidelines here]

## License

[Add license information here]
