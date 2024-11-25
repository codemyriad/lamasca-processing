import os
from pathlib import Path

# File extensions
JPEG_EXTENSION = ".jpeg"

# Model paths
NEWSPAPER_MODEL_PATH = "lp://NewspaperNavigator/faster_rcnn_R_50_FPN_3x/config"

# Categories
NEWSPAPER_CATEGORIES = [
    {"id": 0, "name": "Photograph"},
    {"id": 1, "name": "Illustration"},
    {"id": 2, "name": "Map"},
    {"id": 3, "name": "Comics/Cartoon"},
    {"id": 4, "name": "Editorial Cartoon"},
    {"id": 5, "name": "Headline"},
    {"id": 6, "name": "Advertisement"},
    {"id": 7, "name": "SubHeadline"},
    {"id": 8, "name": "Text"},
    {"id": 9, "name": "Author"},
    {"id": 10, "name": "PageTitle"},
    {"id": 11, "name": "Date"},
    {"id": 12, "name": "PageNumber"},
]

# Create NEWSPAPER_LABEL_MAP from NEWSPAPER_CATEGORIES
NEWSPAPER_LABEL_MAP = {cat["id"]: cat["name"] for cat in NEWSPAPER_CATEGORIES}

# UI XML
UI_CONFIG_XML = (Path(__file__).parent / "ui.xml").read_text()
