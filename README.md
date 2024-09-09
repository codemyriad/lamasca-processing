# LP-LabelStudio

## Important Note for Detectron2 Users

To make this project work correctly, you need to modify the `detection_checkpoint.py` file in the Detectron2 library. This modification is necessary to solve a problem with Dropbox URLs.

Add the following line in the `detection_checkpoint.py` file:

```python
queries.pop("dl", None) # Added by Silvio to solve problem with dropbox urls
```

This line should be added in the appropriate location within the file, typically where URL queries are being processed.

## Usage

To process newspaper pages and generate Label Studio annotations:

```bash
python -m lp_labelstudio process_newspaper /tmp/newspapers/lamasca-pages/1994/lamasca-1994-01-19/
```

This command will process all PNG images in the specified directory, treating them as newspaper pages. It will generate annotation JSON files next to each image.

For example, if you have newspaper pages in the directory `/tmp/newspapers/lamasca-pages/1994/lamasca-1994-01-19/`, you can run:

```bash
python -m lp_labelstudio process_newspaper /tmp/newspapers/lamasca-pages/1994/lamasca-1994-01-19/
```

## Installation

[Add installation instructions here]

## Contributing

[Add contribution guidelines here]

## License

[Add license information here]
