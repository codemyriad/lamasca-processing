from typing import List, Dict, Optional
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse
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

class NewModel(LabelStudioMLBase):
    """Custom ML Backend model"""
    
    def setup(self):
        """Configure any parameters of your model here"""
        self.set("model_version", "0.0.1")
        try:
            self.model = lp.models.Detectron2LayoutModel(NEWSPAPER_MODEL_PATH)
            logger.info("ML model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ML model: {str(e)}")
            self.model = None

    def download_image(self, url):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {str(e)}")
            raise

    @lru_cache(maxsize=100)
    def get_cached_predictions(self, image_url):
        # This function caches predictions for the last 100 unique image URLs
        image = self.download_image(image_url)
        img_width, img_height = image.size

        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            image.save(tmp_file, format='JPEG')
            tmp_file_path = tmp_file.name
            layout = process_single_image(tmp_file_path, self.model)

        return convert_to_label_studio_format(layout, img_width, img_height, image_url)

    def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
        """Write your inference logic here"""
        predictions = []
        for task in tasks:
            image_url = task['data']['image']
            logger.info(f"Processing image: {image_url}")

            try:
                if self.model is None:
                    raise Exception("ML model not initialized")

                annotations = self.get_cached_predictions(image_url)
                predictions.extend(annotations)

                logger.info(f"Processed image {image_url}. Found {len(annotations)} annotations.")
            except Exception as e:
                logger.error(f"Error processing image {image_url}: {str(e)}")
                return ModelResponse(predictions=[], errors=[str(e)])

        return ModelResponse(predictions=predictions)
    
    def fit(self, event, data, **kwargs):
        """
        This method is called each time an annotation is created or updated
        You can run your logic here to update the model and persist it to the cache
        It is not recommended to perform long-running operations here, as it will block the main thread
        Instead, consider running a separate process or a thread (like RQ worker) to perform the training
        :param event: event type can be ('ANNOTATION_CREATED', 'ANNOTATION_UPDATED', 'START_TRAINING')
        :param data: the payload received from the event (check [Webhook event reference](https://labelstud.io/guide/webhook_reference.html))
        """

        # use cache to retrieve the data from the previous fit() runs
        old_data = self.get('my_data')
        old_model_version = self.get('model_version')
        print(f'Old data: {old_data}')
        print(f'Old model version: {old_model_version}')

        # store new data to the cache
        self.set('my_data', 'my_new_data_value')
        self.set('model_version', 'my_new_model_version')
        print(f'New data: {self.get("my_data")}')
        print(f'New model version: {self.get("model_version")}')

        print('fit() completed successfully.')

