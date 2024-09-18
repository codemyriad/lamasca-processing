import click
import os
import requests
import json
from rich.console import Console
from rich.table import Table

@click.group()
def escriptorium():
    """eScriptorium CLI commands"""
    pass

@escriptorium.command()
def list_projects():
    """List all projects in eScriptorium"""
    api_key, base_url = get_escriptorium_config()
    if not api_key:
        return

@escriptorium.command()
@click.option('--name', required=True, help='Name of the project')
@click.option('--description', default='', help='Description of the project')
def create_project(name, description):
    """Create a new project in eScriptorium"""
    api_key, base_url = get_escriptorium_config()
    if not api_key or not base_url:
        return

    url = f"{base_url.rstrip('/')}/api/projects/"
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

    base_url = os.environ.get('ESCRIPTORIUM_URL', 'http://localhost:8080')
    return api_key, base_url

if __name__ == '__main__':
    escriptorium()
