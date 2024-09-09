# LP-LabelStudio

## Important Note for Detectron2 Users

To make this project work correctly, you need to modify the `detection_checkpoint.py` file in the Detectron2 library. This modification is necessary to solve a problem with Dropbox URLs.

Add the following line in the `detection_checkpoint.py` file:

```python
queries.pop("dl", None) # Added by Silvio to solve problem with dropbox urls
```

This line should be added in the appropriate location within the file, typically where URL queries are being processed.

## Usage

To process images and generate Label Studio annotations:

```bash
python -m lp_labelstudio process_image /path/to/image/directory
```

This command will process all images (PNG, JPG, JPEG) in the specified directory and generate annotation JSON files next to each image.

## Installation

[Add installation instructions here]

## Contributing

[Add contribution guidelines here]

## License

[Add license information here]
