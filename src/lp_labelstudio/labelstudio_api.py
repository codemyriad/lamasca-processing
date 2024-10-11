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
        
        data = response.json()
        
        if isinstance(data, dict) and 'results' in data:
            projects = data['results']
        elif isinstance(data, list):
            projects = data
        else:
            click.echo("Unexpected response format.")
            click.echo(f"Response content: {data}")
            return

        if projects:
            click.echo("Existing projects:")
            for project in projects:
                if isinstance(project, dict) and 'id' in project and 'title' in project:
                    click.echo(f"ID: {project['id']}, Title: {project['title']}")
                else:
                    click.echo(f"Unexpected project format: {project}")
        else:
            click.echo("No projects found.")
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Unable to fetch projects. {str(e)}")
    except ValueError as e:
        click.echo(f"Error: Unable to parse JSON response. {str(e)}")

@projects.command()
@click.argument('project_id', type=int)
@click.pass_context
def delete(ctx, project_id):
    """Delete a project by ID."""
    url = f"{ctx.obj['url']}/api/projects/{project_id}/"
    headers = {
        "Authorization": f"Token {ctx.obj['api_key']}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        
        click.echo(f"Project with ID {project_id} has been successfully deleted.")
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Unable to delete project. {str(e)}")

import json
from pathlib import Path
from .generate_manifest import generate_labelstudio_manifest

@projects.command()
@click.argument('directories', nargs=-1, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--annotations-base-path', required=True, type=click.Path(exists=True, file_okay=False, dir_okay=True), help='Base path for annotations')
@click.pass_context
def create(ctx, directories, annotations_base_path):
    """Create a new project for each specified directory."""
    for directory in directories:
        project_name = Path(directory).name
        click.echo(f"Creating project for directory: {project_name}")

        # Generate manifest file
        generate_labelstudio_manifest([directory], annotations_base_path)
        manifest_path = Path(directory) / "manifest.json"

        # Read UI XML
        ui_xml_path = Path(__file__).parent / "ui.xml"
        with ui_xml_path.open() as f:
            ui_xml = f.read()

        # Create project
        create_url = f"{ctx.obj['url']}/api/projects/"
        headers = {
            "Authorization": f"Token {ctx.obj['api_key']}",
            "Content-Type": "application/json"
        }
        project_data = {
            "title": project_name,
            "label_config": ui_xml
        }
        response = requests.post(create_url, headers=headers, json=project_data)
        response.raise_for_status()
        project_id = response.json()['id']
        click.echo(f"Created project '{project_name}' with ID: {project_id}")

        # Upload tasks
        with manifest_path.open() as f:
            tasks = json.load(f)
        
        tasks_url = f"{ctx.obj['url']}/api/projects/{project_id}/import"
        response = requests.post(tasks_url, headers=headers, json=tasks)
        response.raise_for_status()
        click.echo(f"Uploaded {len(tasks)} tasks to project '{project_name}'")

    click.echo("All projects created successfully.")
