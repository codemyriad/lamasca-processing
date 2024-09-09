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
- `process-newspaper`: Process newspaper pages (PNG images) in a directory.

For example, to process newspaper pages and generate Label Studio annotations:

```bash
python -m lp_labelstudio process-newspaper /tmp/newspapers/lamasca-pages/1994/lamasca-1994-01-19/
```

or

```bash
python src/lp_labelstudio/cli.py process-newspaper /tmp/newspapers/lamasca-pages/1994/lamasca-1994-01-19/
```

These commands will process all PNG images in the specified directory, treating them as newspaper pages. They will generate annotation JSON files next to each image.

## Installation

[Add installation instructions here]

## Contributing

[Add contribution guidelines here]

## License

[Add license information here]
