import click
import os
import requests
from rich.console import Console
from rich.table import Table

@click.group()
def escriptorium():
    """eScriptorium CLI commands"""
    pass

@escriptorium.command()
def list_projects():
    """List all projects in eScriptorium"""
    api_key = os.environ.get('ESCRIPTORIUM_API_KEY')
    if not api_key:
        click.echo("Error: ESCRIPTORIUM_API_KEY environment variable is not set.", err=True)
        return

    base_url = os.environ.get('ESCRIPTORIUM_URL', 'http://localhost:8080')
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

if __name__ == '__main__':
    escriptorium()
