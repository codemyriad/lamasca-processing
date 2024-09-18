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
    if not api_key:
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
        "tags": get_tag_definition()
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

def get_tag_definition():
    url = f"{base_url.rstrip('/')}/api/projects/"
    headers = {
        "Authorization": f"Token {api_key}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if 'results' in data and isinstance(data['results'], list):
            projects = data['results']
            if not projects:
                click.echo("No projects found.")
            else:
                console = Console()
                table = Table(title="eScriptorium Projects")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Name", style="magenta")
                table.add_column("Owner", style="green")
                table.add_column("Documents", style="yellow")
                table.add_column("Created At", style="blue")

                for project in projects:
                    table.add_row(
                        str(project['id']),
                        project['name'],
                        project['owner'],
                        str(project['documents_count']),
                        project['created_at']
                    )

                console.print(table)
        else:
            click.echo(f"Unexpected response format. Response: {data}")
    except requests.RequestException as e:
        click.echo(f"Error: Failed to fetch projects. {str(e)}", err=True)
    except ValueError as e:
        click.echo(f"Error: Failed to parse JSON response. {str(e)}", err=True)

def get_tag_definition():
    return {
        "labels": [
            {"value": "Text", "background": "#c8ffbe", "hint": "Columnar text (article body)"},
            {"value": "Headline", "background": "#d8f1a0", "hint": "The bigger title or the only title"},
            {"value": "SubHeadline", "background": "#dce593", "hint": "The smaller title when there are two"},
            {"value": "Author", "background": "#dce593", "hint": "The bold signature at the bottom or top of an article\nOnly text, no spacer line in this box"},
            {"value": "PageTitle", "background": "#efcb68", "hint": "The title at the very top of the page"},
            {"value": "PageNumber", "background": "#dcc7be", "hint": "The number in the top left or right"},
            {"value": "Date", "background": "#ab7968", "hint": "The date in the top left or right"},
            {"value": "Advertisement", "background": "#f46036"},
            {"value": "Map", "background": "#6d72c3"},
            {"value": "Photograph", "background": "#a8dadc"},
            {"value": "Illustration", "background": "#5941a9", "hint": "Any table, graph or similar"},
            {"value": "Comics/Cartoon", "background": "#e5d4ed", "hidden": True},
            {"value": "Editorial Cartoon", "background": "#0b4f6c"}
        ],
        "relations": [
            {"value": "Flow"},
            {"value": "Title of"}
        ]
    }

if __name__ == '__main__':
    escriptorium()
