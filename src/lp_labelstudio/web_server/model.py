import os

# Set MODEL_DIR to system temporary directory:
# the var is used to find a home for the `cache.db` sqlite3 database
if os.environ.get("MODEL_DIR") is None:
    os.environ["MODEL_DIR"] = "/tmp"

from typing import List, Dict, Optional
from requests_file import FileAdapter
from label_studio_ml.model import LabelStudioMLBase
import layoutparser as lp
from lp_labelstudio.constants import NEWSPAPER_MODEL_PATH, NEWSPAPER_LABEL_MAP
from lp_labelstudio.image_processing import (
    process_single_image,
    convert_to_label_studio_format,
    get_image_size,
)
import logging
import requests
from io import BytesIO
from PIL import Image
import tempfile
import json
from functools import lru_cache


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LayoutParserModel(LabelStudioMLBase):
    """Custom ML Backend model"""

    def setup(self):
        """Configure any parameters of your model here"""
        self.set("model_version", "0.0.1")
        self.model = lp.models.Detectron2LayoutModel(
            NEWSPAPER_MODEL_PATH, label_map=NEWSPAPER_LABEL_MAP
        )
        logger.info("ML model initialized successfully")

    def download_image(self, url):
        session = requests.Session()
        session.mount("file://", FileAdapter())
        response = session.get(url, stream=True)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))

    @lru_cache(maxsize=100)
    def get_cached_predictions(self, image_url):
        # This function caches predictions for the last 100 unique image URLs
        image = self.download_image(image_url)
        img_width, img_height = image.size

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            image.save(tmp_file, format="JPEG")
            tmp_file_path = tmp_file.name
            layout = process_single_image(tmp_file_path, self.model)

        return convert_to_label_studio_format(layout, img_width, img_height, image_url)

    def predict(
        self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs
    ) -> "label_studio_ml.response.ModelResponse":
        logger.warn(f"TASKS:\n{json.dumps(tasks, indent=2)}")
        predictions = []

        for task in tasks:
            image_url = task["data"]["ocr"]
            logger.info(f"Processing image: {image_url}")

            if self.model is None:
                raise Exception("ML model not initialized")

            annotations = self.get_cached_predictions(image_url)
            predictions.append(
                [
                    {
                        "result": annotations["predictions"][0],
                    }
                ]
            )

            logger.info(
                f"Processed image {image_url}. Found {len(annotations)} annotations."
            )
        logger.warn(f"Results:\n{json.dumps(predictions, indent=2)}")
        from label_studio_ml.response import ModelResponse

        response = ModelResponse(predictions=predictions)
        return response

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
        old_data = self.get("my_data")
        old_model_version = self.get("model_version")
        print(f"Old data: {old_data}")
        print(f"Old model version: {old_model_version}")

        # store new data to the cache
        self.set("my_data", "my_new_data_value")
        self.set("model_version", "my_new_model_version")
        print(f'New data: {self.get("my_data")}')
        print(f'New model version: {self.get("model_version")}')

        print("fit() completed successfully.")
