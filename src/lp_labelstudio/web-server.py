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

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the model
model = lp.models.Detectron2LayoutModel(NEWSPAPER_MODEL_PATH)

def download_image(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an exception for bad responses
    return Image.open(BytesIO(response.content))

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    image_url = data['task']['data']['image']

    logger.info(f"Processing image: {image_url}")

    image = download_image(image_url)
    img_width, img_height = image.size

    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
        image.save(tmp_file, format='JPEG')
        tmp_file_path = tmp_file.name
        import pdb; pdb.set_trace()
        layout = process_single_image(tmp_file_path, model)

    annotations = convert_to_label_studio_format(layout, img_width, img_height, image_url)

    logger.info(f"Processed image {image_url}. Found {len(annotations)} annotations.")

    return jsonify(annotations)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
