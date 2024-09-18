import click
import os
import requests
import json
from rich.console import Console
from rich.table import Table
from urllib.parse import urljoin

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
            projects = response.json()
        except json.JSONDecodeError:
            click.echo(f"Error: Received non-JSON response: {response.text}", err=True)
            return

        if not isinstance(projects, list):
            click.echo(f"Error: Unexpected response format. Expected a list of projects, got: {type(projects)}", err=True)
            return

        if not projects:
            click.echo("No projects found.")
            return

        console = Console()
        table = Table(title="eScriptorium Projects")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Description", style="green")

        for project in projects:
            if not isinstance(project, dict):
                click.echo(f"Warning: Skipping invalid project data: {project}", err=True)
                continue
            table.add_row(
                str(project.get('id', 'N/A')),
                project.get('name', 'N/A'),
                (project.get('description', '')[:50] + '...') if project.get('description', '') else 'N/A'
            )

        console.print(table)
    except requests.RequestException as e:
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
    except requests.RequestException as e:
        click.echo(f"Error: Failed to create project. {str(e)}", err=True)

def get_escriptorium_config():
    api_key = os.environ.get('ESCRIPTORIUM_API_KEY')
    if not api_key:
        click.echo("Error: ESCRIPTORIUM_API_KEY environment variable is not set.", err=True)
        return None, None

    base_url = os.environ.get('ESCRIPTORIUM_URL', 'http://localhost:8080/')
    return api_key, base_url

def get_api_url(base_url, endpoint):
    return urljoin(base_url, f"api/{endpoint}")

if __name__ == '__main__':
    escriptorium()
