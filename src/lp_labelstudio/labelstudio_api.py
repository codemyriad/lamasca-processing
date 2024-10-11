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
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        projects = response.json()
        if projects:
            click.echo("Existing projects:")
            for project in projects:
                click.echo(f"ID: {project['id']}, Title: {project['title']}")
        else:
            click.echo("No projects found.")
    else:
        click.echo(f"Error: Unable to fetch projects. Status code: {response.status_code}")
