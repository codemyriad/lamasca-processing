from pathlib import Path

# File extensions
JPEG_EXTENSION = '.jpeg'

# Model paths
NEWSPAPER_MODEL_PATH = 'lp://NewspaperNavigator/faster_rcnn_R_50_FPN_3x/config'

# UI XML
UI_CONFIG_XML = (Path(__file__).parent / "ui.xml").read_text()
