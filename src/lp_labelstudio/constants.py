import os
from pathlib import Path

# File extensions
JPEG_EXTENSION = ".jpeg"

# Model paths
NEWSPAPER_MODEL_PATH = os.environ.get("MODEL_PATH", "lp://NewspaperNavigator/faster_rcnn_R_50_FPN_3x/config")
NEWSPAPER_LABEL_MAP = {
    0: "Photograph",
    1: "Illustration",
    2: "Map",
    3: "Comics/Cartoon",
    4: "Editorial Cartoon",
    5: "Headline",
    6: "Advertisement",
}

# UI XML
UI_CONFIG_XML = (Path(__file__).parent / "ui.xml").read_text()
