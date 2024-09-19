import pytest
import json
import os
from lp_labelstudio.constants import UI_CONFIG_XML


@pytest.fixture
def client():
    from lp_labelstudio.web_server.model import LayoutParserModel
    from lp_labelstudio.web_server._wsgi import init_app

    app = init_app(model_class=LayoutParserModel)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_predict(client):
    request = {
        "tasks": [
            {
                "id": 51,
                "data": {
                    "ocr": get_full_path("page_01.jpeg"),
                    "pageNumber": 1,
                    "date": "1994-01-12",
                },
                "meta": {},
                "created_at": "2024-09-13T08:27:19.965258Z",
                "updated_at": "2024-09-13T08:27:19.965294Z",
                "is_labeled": False,
                "overlap": 1,
                "inner_id": 14,
                "total_annotations": 0,
                "cancelled_annotations": 0,
                "total_predictions": 0,
                "comment_count": 0,
                "unresolved_comment_count": 0,
                "last_comment_updated_at": None,
                "project": 6,
                "updated_by": None,
                "file_upload": 15,
                "comment_authors": [],
                "annotations": [],
                "predictions": [],
            }
        ],
        # Your labeling configuration here
        "label_config": UI_CONFIG_XML,
    }

    expected_response = {
        "results": [
            {
                # Your expected result here
            }
        ]
    }

    response = client.post(
        "/predict", data=json.dumps(request), content_type="application/json"
    )
    assert response.status_code == 200
    response = json.loads(response.data)
    assert response == expected_response


def get_full_path(filename):
    return "file://" + os.path.join(os.path.dirname(__file__), "test_images", filename)
