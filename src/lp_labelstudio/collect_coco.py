import json
from typing import List, Dict, Any
from datetime import datetime
from lp_labelstudio.constants import NEWSPAPER_CATEGORIES


def collect_coco(json_files: List[str]) -> None:
    """
    Collect COCO data from multiple JSON files and save to a single output file.
    """
    coco_data: Dict[str, Any] = {
        "images": [],
        "categories": NEWSPAPER_CATEGORIES,
        "annotations": [],
        "info": {
            "year": datetime.now().year,
            "version": "1.0",
            "description": "Collected COCO data",
            "contributor": "Label Studio",
            "url": "",
            "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    }

    image_id = 0
    annotation_id = 0
    category_map = {cat["name"]: cat["id"] for cat in NEWSPAPER_CATEGORIES}
    next_category_id = max(cat["id"] for cat in NEWSPAPER_CATEGORIES) + 1

    for file_path in json_files:
        with open(file_path, "r") as f:
            data = json.load(f)
        for item in data:
            if "annotations" not in item:
                continue

            image_annotations = []

            # Process annotations
            if "annotations" in item:
                for annotation in item["annotations"]:
                    for result in annotation["result"]:
                        if "value" in result and "labels" in result["value"]:
                            label = result["value"]["labels"][0]
                            if label not in category_map:
                                category_map[label] = next_category_id
                                coco_data["categories"].append(
                                    {"id": next_category_id, "name": label}
                                )
                                next_category_id += 1

                            coco_annotation = {
                                "id": annotation_id,
                                "image_id": image_id,
                                "category_id": category_map[label],
                                "segmentation": [],
                                "bbox": [
                                    result["value"]["x"],
                                    result["value"]["y"],
                                    result["value"]["width"],
                                    result["value"]["height"],
                                ],
                                "ignore": 0,
                                "iscrowd": 0,
                                "area": result["value"]["width"]
                                * result["value"]["height"],
                            }
                            image_annotations.append(coco_annotation)
                            annotation_id += 1

            # Only add the image and its annotations if there are annotations
            if image_annotations:
                image = {
                    "id": image_id,
                    "width": item["annotations"][0]["result"][0]["original_width"],
                    "height": item["annotations"][0]["result"][0]["original_height"],
                    "file_name": item["data"]["ocr"],
                }
                coco_data["images"].append(image)
                coco_data["annotations"].extend(image_annotations)
                image_id += 1

    # Save the collected COCO data
    with open("/tmp/coco-out.json", "w") as f:
        json.dump(coco_data, f, indent=2)

    print(
        f"COCO data collected from {len(json_files)} files and saved to /tmp/coco-out.json"
    )
    print(f"Total images: {len(coco_data['images'])}")
    print(f"Total annotations: {len(coco_data['annotations'])}")
    print(f"Total categories: {len(coco_data['categories'])}")
    print("Categories:")
    for category in coco_data["categories"]:
        print(f"  - {category['name']} (id: {category['id']})")
