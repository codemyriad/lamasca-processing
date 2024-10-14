import json
from typing import List, Dict, Any
import click

def collect_coco(json_files: List[str]) -> None:
    """
    Collect COCO data from multiple JSON files and save to a single output file.
    """
    coco_data: Dict[str, Any] = {
        "images": [],
        "categories": [],
        "annotations": [],
        "info": {
            "year": 2024,
            "version": "1.0",
            "description": "Collected COCO data",
            "contributor": "Label Studio",
            "url": "",
            "date_created": ""
        }
    }

    image_id = 0
    annotation_id = 0
    category_map = {}

    for file_path in json_files:
        with open(file_path, 'r') as f:
            data = json.load(f)

        for item in data:
            # Process images
            image = {
                "id": image_id,
                "width": item["data"]["ocr"].split("/")[-1].split("x")[0],
                "height": item["data"]["ocr"].split("/")[-1].split("x")[1].split(".")[0],
                "file_name": item["data"]["ocr"]
            }
            coco_data["images"].append(image)

            # Process annotations
            if "annotations" in item:
                for annotation in item["annotations"]:
                    for result in annotation["result"]:
                        if "value" in result and "labels" in result["value"]:
                            label = result["value"]["labels"][0]
                            if label not in category_map:
                                category_map[label] = len(category_map)
                                coco_data["categories"].append({
                                    "id": category_map[label],
                                    "name": label
                                })

                            coco_annotation = {
                                "id": annotation_id,
                                "image_id": image_id,
                                "category_id": category_map[label],
                                "segmentation": [],
                                "bbox": [
                                    result["value"]["x"],
                                    result["value"]["y"],
                                    result["value"]["width"],
                                    result["value"]["height"]
                                ],
                                "ignore": 0,
                                "iscrowd": 0,
                                "area": result["value"]["width"] * result["value"]["height"]
                            }
                            coco_data["annotations"].append(coco_annotation)
                            annotation_id += 1

            image_id += 1

    # Save the collected COCO data
    with open('/tmp/coco-out.json', 'w') as f:
        json.dump(coco_data, f, indent=2)

    click.echo(f"COCO data collected from {len(json_files)} files and saved to /tmp/coco-out.json")
