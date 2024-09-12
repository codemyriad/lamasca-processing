from flask import Flask, request, jsonify
import layoutparser as lp
from lp_labelstudio.constants import NEWSPAPER_MODEL_PATH
from lp_labelstudio.image_processing import process_single_image, convert_to_label_studio_format, get_image_size
import logging
import requests
from io import BytesIO
from PIL import Image
import tempfile
import os
from functools import lru_cache

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the model
try:
    model = lp.models.Detectron2LayoutModel(NEWSPAPER_MODEL_PATH)
    logger.info("ML model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ML model: {str(e)}")
    model = None

def download_image(url):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        logger.error(f"Failed to download image from {url}: {str(e)}")
        raise

@lru_cache(maxsize=100)
def get_cached_predictions(image_url):
    # This function caches predictions for the last 100 unique image URLs
    image = download_image(image_url)
    img_width, img_height = image.size

    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
        image.save(tmp_file, format='JPEG')
        tmp_file_path = tmp_file.name
        layout = process_single_image(tmp_file_path, model)

    return convert_to_label_studio_format(layout, img_width, img_height, image_url)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    image_url = data['task']['data']['image']

    logger.info(f"Processing image: {image_url}")

    try:
        if model is None:
            raise Exception("ML model not initialized")

        annotations = get_cached_predictions(image_url)

        logger.info(f"Processed image {image_url}. Found {len(annotations)} annotations.")
        return jsonify(annotations)
    except Exception as e:
        logger.error(f"Error processing image {image_url}: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
