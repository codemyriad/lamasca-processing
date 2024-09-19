import os
import requests
import json
import click
from rich.console import Console
from lp_labelstudio.escriptorium_cli import (
    get_escriptorium_config,
    get_api_url,
    escriptorium,
)


@escriptorium.command()
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--replace-from", required=True, help="String to replace in local paths")
@click.option("--replace-to", required=True, help="String to replace with in URLs")
@click.option(
    "--project-id",
    required=True,
    help="ID or slug of the project to add the document to",
)
@click.option("--name", required=True, help="Name of the document")
@click.option("--main-script", default="Latin", help="Main script of the document")
def create_document(directory, replace_from, replace_to, project_id, name, main_script):
    """Create a new document in eScriptorium"""
    api_key, base_url = get_escriptorium_config()
    if not api_key or not base_url:
        return

    url = get_api_url(base_url, "documents/")
    headers = {"Authorization": f"Token {api_key}", "Accept": "application/json"}

    # Prepare the data for the POST request
    data = {
        "name": name,
        "project": project_id,
        "main_script": main_script,
    }

    console = Console()
    try:
        # Create the document
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        document = response.json()
        document_id = document["id"]
        console.print(f"Document created successfully!", style="green")
        console.print(f"Document ID: {document_id}", style="cyan")
        console.print(f"Document Name: {document['name']}", style="magenta")

        # Upload parts (images)
        parts_url = get_api_url(base_url, f"documents/{document_id}/parts/")
        headers["Content-Type"] = "multipart/form-data"

        parts_added = 0
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".tif")):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory)
                    url_path = relative_path.replace(replace_from, replace_to)

                    with open(file_path, "rb") as image_file:
                        files = {"image": (file, image_file)}
                        data = {
                            "name": file,
                            "document": document_id,
                            "order": parts_added + 1,
                        }
                        response = requests.post(
                            parts_url, headers=headers, data=data, files=files
                        )
                        response.raise_for_status()
                        parts_added += 1
                        console.print(f"Uploaded part: {file}", style="blue")

        console.print(f"Number of parts added: {parts_added}", style="yellow")
    except requests.RequestException as e:
        console.print("\nDebugging information:", style="bold")
        console.print(f"API URL: {url}", style="dim")
        console.print(f"Headers: {headers}", style="dim")
        console.print("Request data:", style="dim")
        console.print(json.dumps(data, indent=2), style="dim")
        console.print(
            f"[red]Error: Failed to create document or upload parts. {str(e)}[/red]"
        )
        if hasattr(e, "response") and e.response is not None:
            console.print(
                f"Response status code: {e.response.status_code}", style="yellow"
            )
            console.print(f"Response content: {e.response.text}", style="yellow")
