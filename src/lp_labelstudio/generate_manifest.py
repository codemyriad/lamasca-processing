import click
import os
import json
from typing import List, Dict, Any
from collections import defaultdict

@click.command()
@click.argument('directories', nargs=-1, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('-o', '--output', type=click.Path(file_okay=True, dir_okay=False), required=True, help='Output JSON manifest file')
@click.option('-n', '--max-issues', type=int, default=None, help='Maximum number of issues to include')
def generate_manifest(directories: List[str], output: str, max_issues: int) -> None:
    """Generate a Label Studio JSON manifest file for a project, including newspaper issues with OCR/segmentation."""
    manifest: List[Dict[str, Any]] = []
    total_issues: int = 0

    for directory in directories:
        if directory.endswith('/'):
            directory = directory[:-1]
        if max_issues is not None and total_issues >= max_issues:
            break

        publication_name: str = os.path.basename(directory)
        jpeg_files: List[str] = [f for f in os.listdir(directory) if f.lower().endswith('.jpeg')]

        for jpeg_file in jpeg_files:
            image_path: str = os.path.join(directory, jpeg_file)
            json_path: str = os.path.splitext(image_path)[0] + '_annotations.json'

            if not os.path.exists(json_path):
                click.echo(click.style(f"Warning: Annotation file not found for {image_path}", fg="yellow"))
                continue

            with open(json_path, 'r') as f:
                predictions: Dict[str, Any] = json.load(f)["annotations"]

            task_item: Dict[str, Any] = {
                "id": len(manifest) + 1,
                "annotations": [],
                "file_upload": os.path.basename(image_path),
                "drafts": [],
                "predictions": [],
                "data": {
                    "ocr": os.path.abspath(image_path)
                },
                "meta": {},
                "created_at": "",
                "updated_at": "",
                "inner_id": len(manifest) + 1,
                "total_annotations": 0,
                "cancelled_annotations": 0,
                "total_predictions": 0,
                "comment_count": 0,
                "unresolved_comment_count": 0,
                "last_comment_updated_at": None,
                "project": 1,
                "updated_by": 1,
                "comment_authors": []
            }

            # Add the first annotation from the JSON file if it exists
            if predictions and len(predictions) > 0:
                first_prediction = predictions[0]
                task_item["predictions"].append({
                    "id": 1,
                    "completed_by": 1,
                    "result": first_prediction.get("result", []),
                    "was_cancelled": False,
                    "ground_truth": False,
                    "created_at": "",
                    "updated_at": "",
                    "lead_time": 0,
                    "prediction": {},
                    "result_count": 0,
                    "task": len(manifest) + 1,
                    "project": 1,
                    "updated_by": 1,
                    "parent_prediction": None,
                    "parent_annotation": None
                })
                task_item["total_predictions"] = 1
            else:
                click.echo(click.style(f"Warning: No annotations found for {image_path}", fg="yellow"))

            manifest.append(task_item)

        total_issues += 1

    with open(output, 'w') as f:
        json.dump(manifest, f, indent=2)

    click.echo(click.style(f"Manifest file generated: {output}", fg="green"))
    click.echo(click.style(f"Total issues included: {total_issues}", fg="green"))
    click.echo(click.style(f"Total pages included: {len(manifest)}", fg="green"))

def read_xml_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read()
