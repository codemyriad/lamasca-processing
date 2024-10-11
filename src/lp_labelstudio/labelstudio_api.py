import click
import os
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

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
    """List existing projects with annotation summaries."""
    url = f"{ctx.obj['url']}/api/projects/"
    headers = {
        "Authorization": f"Token {ctx.obj['api_key']}",
        "Content-Type": "application/json"
    }
    
    console = Console()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if isinstance(data, dict) and 'results' in data:
            projects = data['results']
        elif isinstance(data, list):
            projects = data
        else:
            console.print("[bold red]Unexpected response format.[/bold red]")
            console.print(f"Response content: {data}")
            return

        if projects:
            table = Table(title="Existing Projects")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Tasks", style="green")
            table.add_column("Annotations", style="yellow")
            table.add_column("Completed", style="blue")

            for project in projects:
                if isinstance(project, dict) and 'id' in project and 'title' in project:
                    project_id = project['id']
                    project_title = project['title']
                    
                    # Fetch project details
                    project_url = f"{ctx.obj['url']}/api/projects/{project_id}/"
                    project_response = requests.get(project_url, headers=headers)
                    project_response.raise_for_status()
                    project_details = project_response.json()
                    
                    tasks_count = project_details.get('task_number', 0)
                    total_annotations = project_details.get('total_annotations_number', 0)
                    completed_tasks = project_details.get('num_tasks_with_annotations', 0)
                    
                    table.add_row(
                        str(project_id),
                        project_title,
                        str(tasks_count),
                        str(total_annotations),
                        f"{completed_tasks}/{tasks_count}"
                    )
                else:
                    console.print(f"[bold red]Unexpected project format:[/bold red] {project}")
            
            console.print(table)
        else:
            console.print("[bold yellow]No projects found.[/bold yellow]")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] Unable to fetch projects. {str(e)}")
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] Unable to parse JSON response. {str(e)}")

@projects.command()
@click.argument('project_ids', nargs=-1, type=int)
@click.pass_context
def delete(ctx, project_ids):
    """Delete one or more projects by ID."""
    headers = {
        "Authorization": f"Token {ctx.obj['api_key']}",
        "Content-Type": "application/json"
    }
    
    for project_id in project_ids:
        url = f"{ctx.obj['url']}/api/projects/{project_id}/"
        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            click.echo(f"Project with ID {project_id} has been successfully deleted.")
        except requests.exceptions.RequestException as e:
            click.echo(f"Error: Unable to delete project {project_id}. {str(e)}")

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

@projects.command()
@click.argument('project_id', type=int)
@click.pass_context
def view(ctx, project_id):
    """View details of a specific project."""
    url = f"{ctx.obj['url']}/api/projects/{project_id}/"
    tasks_url = f"{ctx.obj['url']}/api/tasks?project={project_id}"
    headers = {
        "Authorization": f"Token {ctx.obj['api_key']}",
        "Content-Type": "application/json"
    }
    
    console = Console()
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        project = response.json()
        
        # Extract labels from label_config
        import xml.etree.ElementTree as ET
        root = ET.fromstring(project.get('label_config', ''))
        labels = [label.get('value') for label in root.findall(".//Label")]
        
        title = Text(f"Project Details: {project['title']}", style="bold magenta")
        panel = Panel(
            Text.assemble(
                ("ID: ", "bold cyan"), f"{project.get('id', 'N/A')}\n",
                ("Description: ", "bold green"), f"{project.get('description', 'N/A')}\n",
                ("Created: ", "bold yellow"), f"{project.get('created_at', 'N/A')}\n",
                ("Updated: ", "bold yellow"), f"{project.get('updated_at', 'N/A')}\n",
                ("Labels: ", "bold blue"), f"{', '.join(labels)}\n",
                ("Task Number: ", "bold red"), f"{project.get('task_number', 0)}\n",
                ("Completed Tasks: ", "bold red"), f"{project.get('num_tasks_with_annotations', 0)}"
            ),
            title=title,
            expand=False
        )
        
        console.print(panel)
        
        # Fetch and display tasks
        tasks_response = requests.get(tasks_url, headers=headers)
        tasks_response.raise_for_status()
        tasks = tasks_response.json()
        
        if isinstance(tasks, dict) and 'results' in tasks:
            tasks = tasks['results']
        
        if tasks:
            tasks_table = Table(title="Tasks")
            tasks_table.add_column("ID", style="cyan")
            tasks_table.add_column("Data", style="magenta")
            tasks_table.add_column("Annotations", style="green")
            
            for task in tasks:
                tasks_table.add_row(
                    str(task['id']),
                    str(task.get('data', {})),
                    str(len(task.get('annotations', [])))
                )
            
            console.print(tasks_table)
        else:
            console.print("[bold yellow]No tasks found for this project.[/bold yellow]")
        
        # Display members if available
        if 'members' in project and project['members']:
            members_table = Table(title="Project Members")
            members_table.add_column("ID", style="cyan")
            members_table.add_column("Email", style="magenta")
            members_table.add_column("First Name", style="green")
            members_table.add_column("Last Name", style="green")
            
            for member in project['members']:
                members_table.add_row(
                    str(member['id']),
                    member['email'],
                    member.get('first_name', 'N/A'),
                    member.get('last_name', 'N/A')
                )
            
            console.print(members_table)
        
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Error:[/bold red] Unable to fetch project details. {str(e)}")
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] Unable to parse JSON response. {str(e)}")
