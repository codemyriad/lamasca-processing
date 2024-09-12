from flask import Flask, request, jsonify
import layoutparser as lp
from lp_labelstudio.constants import NEWSPAPER_MODEL_PATH
from lp_labelstudio.image_processing import process_single_image, convert_to_label_studio_format, get_image_size
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the model
model = lp.models.Detectron2LayoutModel(NEWSPAPER_MODEL_PATH)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    image_url = data['task']['data']['image']

    logger.info(f"Processing image: {image_url}")

    # Process the image
    layout = process_single_image(image_url, model)
    img_width, img_height = get_image_size(image_url)
    
    # Convert to Label Studio format
    annotations = convert_to_label_studio_format(layout, img_width, img_height, image_url)

    logger.info(f"Processed image {image_url}. Found {len(annotations)} annotations.")

    return jsonify(annotations)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
