import click
import os
import requests

@click.group()
@click.option('--url', required=True, envvar='LABELSTUDIO_URL', help='Label Studio API URL')
@click.option('--api-key', required=True, envvar='LABELSTUDIO_API_KEY', help='Label Studio API Key')
@click.pass_context
def labelstudio_api(ctx, url, api_key):
    """Command group for Label Studio API operations."""
    ctx.ensure_object(dict)
    ctx.obj['url'] = url
    ctx.obj['api_key'] = api_key

@labelstudio_api.group()
@click.pass_context
def projects(ctx):
    """Manage Label Studio projects."""
    pass

@projects.command()
@click.pass_context
def list(ctx):
    """List existing projects."""
    url = f"{ctx.obj['url']}/api/projects/"
    headers = {
        "Authorization": f"Token {ctx.obj['api_key']}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        projects = response.json()
        if isinstance(projects, list) and projects:
            click.echo("Existing projects:")
            for project in projects:
                if isinstance(project, dict) and 'id' in project and 'title' in project:
                    click.echo(f"ID: {project['id']}, Title: {project['title']}")
                else:
                    click.echo(f"Unexpected project format: {project}")
        elif isinstance(projects, dict):
            click.echo("Unexpected response format. Received a dictionary instead of a list.")
            click.echo(f"Response content: {projects}")
        else:
            click.echo("No projects found or unexpected response format.")
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Unable to fetch projects. {str(e)}")
    except ValueError as e:
        click.echo(f"Error: Unable to parse JSON response. {str(e)}")
