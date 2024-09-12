Preprocess PDF files for OCR and fine tuning/training

Typical usage:
python directory.py /tmp/newspapers/lamasca/1994/ /tmp/newspapers/lamasca-pages/1994/ --force

This will process all the PDF files in /tmp/newspapers/lamasca/1994/ and save the output in /tmp/newspapers/lamasca-pages/1994.

Each page will be converted to greyscale, deskewed, and saved as a separate image file.
