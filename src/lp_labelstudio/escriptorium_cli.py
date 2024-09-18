import click
import os
import requests

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

    url = "https://escriptorium.fr/api/projects/"
    headers = {
        "Authorization": f"Token {api_key}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        projects = response.json()

        if not projects:
            click.echo("No projects found.")
        else:
            click.echo("Projects:")
            for project in projects:
                click.echo(f"- {project['name']} (ID: {project['id']})")
    except requests.RequestException as e:
        click.echo(f"Error: Failed to fetch projects. {str(e)}", err=True)

if __name__ == '__main__':
    escriptorium()
