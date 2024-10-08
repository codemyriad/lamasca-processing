import click
import os
import requests
import json
from rich.console import Console
from rich.table import Table
from urllib.parse import urljoin, urlparse
from pathlib import Path


@click.group()
def escriptorium():
    """eScriptorium CLI commands"""
    pass


@escriptorium.command()
def list_projects():
    """List all projects in eScriptorium"""
    api_key, base_url = get_escriptorium_config()
    if not api_key or not base_url:
        return

    url = get_api_url(base_url, "projects/")
    headers = {"Authorization": f"Token {api_key}", "Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        try:
            data = response.json()
        except json.JSONDecodeError:
            click.echo(f"Error: Received non-JSON response: {response.text}", err=True)
            return

        if isinstance(data, dict) and "results" in data:
            projects = data["results"]
        elif isinstance(data, list):
            projects = data
        else:
            click.echo(
                f"Error: Unexpected response format. Unable to extract projects list.",
                err=True,
            )
            return

        if not projects:
            click.echo("No projects found.")
            return

        console = Console()
        table = Table(title="eScriptorium Projects")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Slug", style="yellow")
        table.add_column("Description", style="green")

        for project in projects:
            if not isinstance(project, dict):
                click.echo(
                    f"Warning: Skipping invalid project data: {project}", err=True
                )
                continue
            description = project.get("description", "")
            if description:
                description = (
                    (description[:47] + "...") if len(description) > 50 else description
                )
            else:
                description = "N/A"

            table.add_row(
                str(project.get("id", "N/A")),
                project.get("name", "N/A"),
                project.get("slug", "N/A"),
                description,
            )

        console.print(table)
    except requests.RequestException as e:
        if "NameResolutionError" in str(e):
            click.echo(
                f"Error: Failed to resolve the eScriptorium URL. Please check if the URL is correct and accessible.",
                err=True,
            )
        elif "ConnectionError" in str(e):
            click.echo(
                f"Error: Failed to connect to eScriptorium. Please check if the server is running and accessible.",
                err=True,
            )
        else:
            click.echo(f"Error: Failed to list projects. {str(e)}", err=True)


@escriptorium.command()
@click.option("--name", required=True, help="Name of the project")
@click.option("--description", default="", help="Description of the project")
def create_project(name, description):
    """Create a new project in eScriptorium"""
    api_key, base_url = get_escriptorium_config()
    if not api_key or not base_url:
        return

    url = get_api_url(base_url, "projects/")
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = {
        "name": name,
        "description": description,
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        project = response.json()
        console = Console()
        console.print(f"Project created successfully!", style="green")
        console.print(f"Project ID: {project['id']}", style="cyan")
        console.print(f"Project Name: {project['name']}", style="magenta")
        console.print(
            f"Project Description: {project.get('description') or 'N/A'}",
            style="yellow",
        )

        # Print the raw response for debugging
        console.print("Raw response:", style="dim")
        console.print(response.text, style="dim")

        # Print the parsed JSON response
        console.print("Parsed JSON response:", style="dim")
        console.print(json.dumps(project, indent=2), style="dim")
    except requests.RequestException as e:
        click.echo(f"Error: Failed to create project. {str(e)}", err=True)


@escriptorium.command()
@click.argument("project_pk", type=str)
def list_documents(project_pk):
    """List all documents in a project"""
    api_key, base_url = get_escriptorium_config()
    if not api_key or not base_url:
        return

    url = get_api_url(base_url, f"documents/?project={project_pk}")
    headers = {"Authorization": f"Token {api_key}", "Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        try:
            data = response.json()
        except json.JSONDecodeError:
            click.echo(f"Error: Received non-JSON response: {response.text}", err=True)
            return

        console = Console()

        if not isinstance(data, dict) or "results" not in data:
            console.print(
                f"[red]Error: Unexpected response format. Expected a dictionary with 'results' key.[/red]"
            )
            console.print("Raw response:", style="dim")
            console.print(response.text, style="dim")
            return

        documents = data["results"]

        if not documents:
            console.print("[yellow]No documents found in this project.[/yellow]")
            return

        table = Table(title=f"Documents in Project: {project_pk}")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Created At", style="green")
        table.add_column("Main Script", style="yellow")
        table.add_column("Parts Count", style="blue")

        for document in documents:
            if not isinstance(document, dict):
                console.print(
                    f"[yellow]Warning: Skipping invalid document data: {document}[/yellow]"
                )
                continue
            table.add_row(
                str(document.get("pk", "N/A")),
                document.get("name", "N/A"),
                document.get("created_at", "N/A"),
                document.get("main_script", "N/A"),
                str(document.get("parts_count", "N/A")),
            )

        console.print(table)

        # Print pagination information
        console.print(f"\nTotal documents: {data.get('count', 'N/A')}", style="bold")
        if data.get("next"):
            console.print(
                "There are more documents. Use pagination to see them.", style="italic"
            )

    except requests.RequestException as e:
        console = Console()
        console.print(f"[red]Error: Failed to list documents. {str(e)}[/red]")
        if hasattr(e, "response") and e.response is not None:
            console.print(
                f"Response status code: {e.response.status_code}", style="yellow"
            )
            console.print(f"Response content: {e.response.text}", style="yellow")


@escriptorium.command()
@click.argument("document_id", type=int)
def list_images(document_id):
    """List all images in a document"""
    api_key, base_url = get_escriptorium_config()
    if not api_key or not base_url:
        return

    url = get_api_url(base_url, f"documents/{document_id}/parts/")
    headers = {"Authorization": f"Token {api_key}", "Accept": "application/json"}

    console = Console()

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    document = response.json()

    table = Table(title=f"Images in Document: {document_id}")
    table.add_column("Part ID", style="cyan")
    table.add_column("Page title", style="magenta")
    table.add_column("Image size", style="green")
    table.add_column("Order", style="yellow")

    for part in document["results"]:
        image_size = "x".join(map(str, part["image"]["size"]))
        table.add_row(
            str(part.get("id", "N/A")),
            part.get("name", "N/A"),
            image_size,
            str(part.get("order", "N/A")),
        )

    console.print(table)
    console.print(f"\nTotal images: {len(document['results'])}", style="bold")


def get_escriptorium_config():
    api_key = os.environ.get("ESCRIPTORIUM_API_KEY")
    if not api_key:
        click.echo(
            "Error: ESCRIPTORIUM_API_KEY environment variable is not set.", err=True
        )
        return None, None

    base_url = os.environ.get("ESCRIPTORIUM_URL", "http://localhost:8080/")

    # Validate the URL
    parsed_url = urlparse(base_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        click.echo(
            f"Error: Invalid ESCRIPTORIUM_URL '{base_url}'. Please provide a valid URL including the scheme (http:// or https://).",
            err=True,
        )
        return None, None

    return api_key, base_url


def get_api_url(base_url, endpoint):
    return urljoin(base_url, f"api/{endpoint}")


if __name__ == "__main__":
    escriptorium()


import lp_labelstudio.escriptorium_cli_create_document
