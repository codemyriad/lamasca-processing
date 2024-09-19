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
    headers = {
        "Authorization": f"Token {api_key}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        try:
            data = response.json()
        except json.JSONDecodeError:
            click.echo(f"Error: Received non-JSON response: {response.text}", err=True)
            return

        if isinstance(data, dict) and 'results' in data:
            projects = data['results']
        elif isinstance(data, list):
            projects = data
        else:
            click.echo(f"Error: Unexpected response format. Unable to extract projects list.", err=True)
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
                click.echo(f"Warning: Skipping invalid project data: {project}", err=True)
                continue
            description = project.get('description', '')
            if description:
                description = (description[:47] + '...') if len(description) > 50 else description
            else:
                description = 'N/A'

            table.add_row(
                str(project.get('id', 'N/A')),
                project.get('name', 'N/A'),
                project.get('slug', 'N/A'),
                description
            )

        console.print(table)
    except requests.RequestException as e:
        if "NameResolutionError" in str(e):
            click.echo(f"Error: Failed to resolve the eScriptorium URL. Please check if the URL is correct and accessible.", err=True)
        elif "ConnectionError" in str(e):
            click.echo(f"Error: Failed to connect to eScriptorium. Please check if the server is running and accessible.", err=True)
        else:
            click.echo(f"Error: Failed to list projects. {str(e)}", err=True)

@escriptorium.command()
@click.option('--name', required=True, help='Name of the project')
@click.option('--description', default='', help='Description of the project')
def create_project(name, description):
    """Create a new project in eScriptorium"""
    api_key, base_url = get_escriptorium_config()
    if not api_key or not base_url:
        return

    url = get_api_url(base_url, "projects/")
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
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
        console.print(f"Project Description: {project.get('description') or 'N/A'}", style="yellow")

        # Print the raw response for debugging
        console.print("Raw response:", style="dim")
        console.print(response.text, style="dim")

        # Print the parsed JSON response
        console.print("Parsed JSON response:", style="dim")
        console.print(json.dumps(project, indent=2), style="dim")
    except requests.RequestException as e:
        click.echo(f"Error: Failed to create project. {str(e)}", err=True)

@escriptorium.command()
@click.argument('project_pk', type=str)
def list_documents(project_pk):
    """List all documents in a project"""
    api_key, base_url = get_escriptorium_config()
    if not api_key or not base_url:
        return

    url = get_api_url(base_url, f"documents/?project={project_pk}")
    headers = {
        "Authorization": f"Token {api_key}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            click.echo(f"Error: Received non-JSON response: {response.text}", err=True)
            return

        console = Console()
        
        if not isinstance(data, dict) or 'results' not in data:
            console.print(f"[red]Error: Unexpected response format. Expected a dictionary with 'results' key.[/red]")
            console.print("Raw response:", style="dim")
            console.print(response.text, style="dim")
            return

        documents = data['results']

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
                console.print(f"[yellow]Warning: Skipping invalid document data: {document}[/yellow]")
                continue
            table.add_row(
                str(document.get('pk', 'N/A')),
                document.get('name', 'N/A'),
                document.get('created_at', 'N/A'),
                document.get('main_script', 'N/A'),
                str(document.get('parts_count', 'N/A'))
            )

        console.print(table)

        # Print pagination information
        console.print(f"\nTotal documents: {data.get('count', 'N/A')}", style="bold")
        if data.get('next'):
            console.print("There are more documents. Use pagination to see them.", style="italic")

    except requests.RequestException as e:
        console = Console()
        console.print(f"[red]Error: Failed to list documents. {str(e)}[/red]")
        if hasattr(e, 'response') and e.response is not None:
            console.print(f"Response status code: {e.response.status_code}", style="yellow")
            console.print(f"Response content: {e.response.text}", style="yellow")

@escriptorium.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--replace-from', required=True, help='String to replace in local paths')
@click.option('--replace-to', required=True, help='String to replace with in URLs')
@click.option('--project-id', required=True, help='ID or slug of the project to add the document to')
@click.option('--name', required=True, help='Name of the document')
@click.option('--main-script', default='Latin', help='Main script of the document')
def create_document(directory, replace_from, replace_to, project_id, name, main_script):
    """Create a new document in eScriptorium"""
    api_key, base_url = get_escriptorium_config()
    if not api_key or not base_url:
        return

    # Convert project_id to int if it's a numeric string
    try:
        project_id = int(project_id)
    except ValueError:
        # If it's not a number, assume it's a slug and leave it as a string
        pass

    # Get list of image files in the directory
    image_files = list(Path(directory).glob('**/*.jpeg')) + list(Path(directory).glob('**/*.png'))

    if not image_files:
        click.echo("Error: No image files found in the specified directory.", err=True)
        return

    # Create image URLs
    image_urls = [str(file).replace(replace_from, replace_to) for file in image_files]

    # Prepare data for API request
    url = get_api_url(base_url, f"documents/")
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "name": name,
        "main_script": main_script,
        "parts": [{"image": url} for url in image_urls]
    }

    # Always include the project field, and include project_slug if it's not a numeric ID
    data["project"] = project_id
    if not isinstance(project_id, int):
        data["project_slug"] = project_id

    console = Console()
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        document = response.json()
        console.print(f"Document created successfully!", style="green")
        console.print(f"Document PK: {document.get('pk', 'N/A')}", style="cyan")
        console.print(f"Document Name: {document.get('name', 'N/A')}", style="magenta")
        console.print(f"Project: {document.get('project', 'N/A')}", style="yellow")
        console.print(f"Main Script: {document.get('main_script', 'N/A')}", style="yellow")
        console.print(f"Created At: {document.get('created_at', 'N/A')}", style="yellow")

        if 'parts' in document:
            console.print(f"Number of parts: {len(document['parts'])}", style="yellow")
        else:
            console.print("Number of parts: Not available in the response", style="yellow")

        console.print("\nFull Document Details:", style="bold")
        console.print(json.dumps(document, indent=2), style="dim")
    except requests.RequestException as e:
        console.print(f"Error: Failed to create document. {str(e)}", style="red")
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            console.print(f"Response status code: {status_code}", style="yellow")
            console.print(f"Response content: {e.response.text}", style="yellow")
            if status_code == 400:
                console.print("Bad Request: The server could not understand the request.", style="red")
            elif status_code == 401:
                console.print("Unauthorized: Authentication failed. Check your API key.", style="red")
            elif status_code == 403:
                console.print("Forbidden: You don't have permission to create documents in this project.", style="red")
            elif status_code == 404:
                console.print("Not Found: The specified project or endpoint could not be found.", style="red")
            elif status_code == 500:
                console.print("Internal Server Error: Something went wrong on the server side.", style="red")
            try:
                response_json = e.response.json()
                console.print("Detailed error information:", style="yellow")
                console.print(json.dumps(response_json, indent=2), style="yellow")
            except json.JSONDecodeError:
                console.print("Unable to parse response as JSON", style="yellow")
    except Exception as e:
        console.print(f"An unexpected error occurred: {str(e)}", style="red")
    finally:
        console.print("\nRequest Details (for debugging):", style="dim")
        console.print(f"URL: {url}", style="dim")
        console.print("Headers:", style="dim")
        for key, value in headers.items():
            if key.lower() == 'authorization':
                console.print(f"  {key}: Token <redacted>", style="dim")
            else:
                console.print(f"  {key}: {value}", style="dim")
        console.print("Data:", style="dim")
        console.print(json.dumps(data, indent=2), style="dim")

def get_escriptorium_config():
    api_key = os.environ.get('ESCRIPTORIUM_API_KEY')
    if not api_key:
        click.echo("Error: ESCRIPTORIUM_API_KEY environment variable is not set.", err=True)
        return None, None

    base_url = os.environ.get('ESCRIPTORIUM_URL', 'http://localhost:8080/')

    # Validate the URL
    parsed_url = urlparse(base_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        click.echo(f"Error: Invalid ESCRIPTORIUM_URL '{base_url}'. Please provide a valid URL including the scheme (http:// or https://).", err=True)
        return None, None

    return api_key, base_url

def get_api_url(base_url, endpoint):
    return urljoin(base_url, f"api/{endpoint}")

if __name__ == '__main__':
    escriptorium()
