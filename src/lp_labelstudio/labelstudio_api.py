import click
import os
import re
import requests
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns

@click.group()
@click.option('--url', required=True, envvar='LABELSTUDIO_URL', help='Label Studio API URL')
@click.option('--api-auth', required=True, envvar='LABELSTUDIO_CREDENTIALS', help='Authorization header value for Label Studio API requests')
@click.pass_context
def labelstudio_api(ctx, url, api_auth):
    """Command group for Label Studio API operations."""
    ctx.ensure_object(dict)
    ctx.obj['url'] = url
    ctx.obj['api_auth'] = api_auth

@labelstudio_api.group()
@click.pass_context
def projects(ctx):
    """Manage Label Studio projects."""
    pass

@projects.command(name="list")
@click.option('--local-root', type=click.Path(exists=True, file_okay=False, dir_okay=True), default=None, envvar='LOCAL_NEWSPAPER_ROOT', help='Local root directory for newspaper files')
@click.pass_context
def list_projects(ctx, local_root):
    """List existing projects with annotation summaries."""
    url = f"{ctx.obj['url']}/api/projects/"
    headers = {
        "Authorization": ctx.obj['api_auth'],
        "Content-Type": "application/json"
    }

    console = Console()
    annotator_tasks = defaultdict(int)
    annotator_projects = defaultdict(int)

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
            table.add_column("Completed", style="bold")
            table.add_column("Local Annotations", style="green")
            table.add_column("To fetch", style="yellow")

            total_annotated_tasks = 0

            # Sort projects by id
            sorted_projects = sorted(projects, key=lambda x: x.get('id', 0))

            for project in sorted_projects:
                if isinstance(project, dict) and 'id' in project and 'title' in project:
                    project_id = project['id']
                    project_title = project['title']

                    # Fetch project details
                    project_url = f"{ctx.obj['url']}/api/projects/{project_id}/"
                    project_response = requests.get(project_url, headers=headers)
                    project_response.raise_for_status()
                    project_details = project_response.json()

                    tasks_count = project_details.get('task_number', 0)
                    completed_tasks = project_details.get('num_tasks_with_annotations', 0)
                    total_annotated_tasks += completed_tasks

                    # Calculate completion percentage and determine color
                    if tasks_count > 0:
                        completion_percentage = (completed_tasks / tasks_count) * 100
                        if completion_percentage == 0:
                            color = "red"
                        elif completion_percentage == 100:
                            color = "green"
                        else:
                            color = f"rgb({int(255 - 2.55 * completion_percentage)},{int(2.55 * completion_percentage)},0)"
                    else:
                        completion_percentage = 0
                        color = "red"

                    completed_str = f"[{color}]{completed_tasks}/{tasks_count} ({completion_percentage:.1f}%)[/{color}]"

                    # Get local annotations info
                    local_annotations, to_fetch, annotators = get_local_annotations_info(local_root, project_title, completed_tasks)
                    # Update global annotator data
                    for annotator, count in annotators.items():
                        annotator_tasks[annotator] += count
                        annotator_projects[annotator] += 1

                    table.add_row(
                        str(project_id),
                        project_title,
                        completed_str,
                        local_annotations,
                        str(to_fetch)
                    )
                else:
                    console.print(f"[bold red]Unexpected project format:[/bold red] {project}")

            console.print(table)
            console.print(Panel(f"[bold green]Total annotated tasks: {total_annotated_tasks}[/bold green]", expand=False))
            if annotator_tasks:
                console.print("\nAnnotator Breakdown:")
                for annotator in annotator_tasks:
                    total_tasks = annotator_tasks[annotator]
                    total_projects = annotator_projects[annotator]
                    console.print(f"{annotator}: {total_tasks} tasks over {total_projects} projects")
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
        "Authorization": ctx.obj['api_auth'],
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
import os
from collections import defaultdict
from pathlib import Path
from .generate_manifest import generate_labelstudio_manifest

def local_dir_name(project_name):
    """Extract the word that includes a date.
    """
    possible_words = project_name.split(' ')
    for word in possible_words:
        match = re.search(r'\d{4}-\d{2}-\d{2}', word)
        if match:
            return word

def get_local_annotations_info(local_root, project_name, remote_annotations_count):
    annotators = {}
    if not local_root:
        return "N/A", remote_annotations_count, annotators

    dir_name = local_dir_name(project_name)
    if not dir_name:
        return "No matching local directory", remote_annotations_count, annotators

    full_path = os.path.join(local_root, dir_name, "annotations")
    if not os.path.exists(full_path):
        return "No local annotations", remote_annotations_count, annotators

    annotators = defaultdict(int)
    local_annotations_count = 0

    for root, dirs, files in os.walk(full_path):
        for file in files:
            if file.endswith('.json'):
                annotator = os.path.basename(os.path.dirname(os.path.join(root, file)))
                annotators[annotator] += 1
                local_annotations_count += 1

    if not annotators:
        return "No annotations found", remote_annotations_count, annotators

    annotator_info = "\n".join(f"{annotator}: {count}" for annotator, count in annotators.items())
    to_fetch = max(0, remote_annotations_count - local_annotations_count)
    return annotator_info, to_fetch, annotators

@projects.command()
@click.argument('directories', nargs=-1, type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--prefix', default='', help='Prefix for the project name')
@click.pass_context
def create(ctx, directories, prefix):
    """Create a new project for each specified directory."""
    generate_labelstudio_manifest(directories)
    for directory in directories:
        base_name = Path(directory).name
        project_name = f"{prefix} {base_name}" if prefix else base_name
        click.echo(f"Creating project for directory: {base_name}")
        click.echo(f"Project name: {project_name}")

        # Generate manifest file
        manifest_path = Path(directory) / "manifest.json"

        # Read UI XML
        ui_xml_path = Path(__file__).parent / "ui.xml"
        with ui_xml_path.open() as f:
            ui_xml = f.read()

        # Create project
        create_url = f"{ctx.obj['url']}/api/projects/"
        headers = {
            "Authorization": ctx.obj['api_auth'],
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
    # ... (existing code remains unchanged)

import json
from difflib import SequenceMatcher, unified_diff

def summarize_changes(old_annotation, new_annotation, verbose=False):
    old_json = json.dumps(old_annotation, sort_keys=True, indent=2)
    new_json = json.dumps(new_annotation, sort_keys=True, indent=2)
    
    if old_json == new_json:
        return "no changes", ""

    # Calculate the similarity ratio
    similarity = SequenceMatcher(None, old_json, new_json).ratio()
    
    # Calculate the change in overall length
    old_length = len(old_json)
    new_length = len(new_json)
    length_diff = new_length - old_length
    
    # Count the number of changed keys at the top level
    changed_keys = sum(1 for k in set(old_annotation.keys()) | set(new_annotation.keys())
                       if old_annotation.get(k) != new_annotation.get(k))
    
    summary = []
    if length_diff != 0:
        summary.append(f"size {'increased' if length_diff > 0 else 'decreased'} by {abs(length_diff)} chars")
    if changed_keys > 0:
        summary.append(f"{changed_keys} top-level keys changed")
    summary.append(f"overall similarity: {similarity:.2%}")
    
    summary_text = ", ".join(summary)
    
    if verbose:
        diff = '\n'.join(unified_diff(
            old_json.splitlines(),
            new_json.splitlines(),
            fromfile='Local',
            tofile='Remote',
            lineterm=''
        ))
        return summary_text, diff
    else:
        return summary_text, ""

@projects.command()
@click.option('--local-root', type=click.Path(exists=True, file_okay=False, dir_okay=True), required=True, envvar='LOCAL_NEWSPAPER_ROOT', help='Local root directory for newspaper files')
@click.option('--verbose', is_flag=True, help='Print detailed differences between local and remote annotations')
@click.pass_context
def fetch(ctx, local_root, verbose):
    """Fetch all remote annotations and update local copies if there are changes."""
    if local_root is None:
        raise Exception("Error: Local root directory is not set. Please set the LOCAL_NEWSPAPER_ROOT environment variable or use the --local-root option.")
    url = f"{ctx.obj['url']}/api/projects/"
    headers = {
        "Authorization": ctx.obj['api_auth'],
        "Content-Type": "application/json"
    }

    console = Console()

    # Fetch all projects
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    projects = response.json()['results']

    for project in projects:
        project_id = project['id']
        project_title = project['title']
        if not project["num_tasks_with_annotations"]:
            continue
        console.print(f"[bold]Fetching annotations for project: {project_title}[/bold]")

        # Fetch tasks for the project
        tasks_url = f"{ctx.obj['url']}/api/tasks?project={project_id}"
        tasks_response = requests.get(tasks_url, headers=headers)
        tasks_response.raise_for_status()
        tasks = tasks_response.json()

        for task in tasks["tasks"]:
            if not task["total_annotations"]:
                continue
            task_id = task['id']
            annotations_url = f"{ctx.obj['url']}/api/tasks/{task_id}/annotations/"
            annotations_response = requests.get(annotations_url, headers=headers)
            annotations_response.raise_for_status()
            annotations = annotations_response.json()

            for annotation in annotations:
                assert annotation["task"] == task["id"]
                annotation["task"] = task
                # Extract necessary information
                annotator_email = extract_email(annotation["created_username"])
                page_number = task['data'].get('pageNumber', 'unknown')
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', project_title)
                date = date_match.group(0) if date_match else 'unknown_date'
                newspaper_name = project_title.split()[0]

                local_path = Path(local_root) / local_dir_name(project_title) / "annotations" / annotator_email
                local_path.mkdir(parents=True, exist_ok=True)
                file_name = f"page{page_number:02d}.json"
                full_path = local_path / file_name

                # Check if the annotation exists locally and compare
                if full_path.exists():
                    with full_path.open('r') as f:
                        local_annotation = json.load(f)
                    
                    if local_annotation != annotation:
                        changes_summary, diff = summarize_changes(local_annotation, annotation, verbose)
                        # Update the local copy if there are changes
                        with full_path.open('w') as f:
                            json.dump(annotation, f, indent=2)
                        console.print(f"Updated existing annotation: {full_path} ({changes_summary})")
                        if verbose and diff:
                            console.print("Detailed differences:")
                            console.print(diff)
                    else:
                        console.print(f"No changes in annotation: {full_path}")
                else:
                    # Save the new annotation locally
                    with full_path.open('w') as f:
                        json.dump(annotation, f, indent=2)
                    console.print(f"Saved new annotation: {full_path}")
                    if verbose:
                        console.print("New annotation content:")
                        console.print(json.dumps(annotation, indent=2))

    console.print("[bold green]Finished fetching and updating annotations.[/bold green]")


@projects.command()
@click.argument('project_id', type=int)
@click.pass_context
def view(ctx, project_id):
    """View details of a specific project."""
    url = f"{ctx.obj['url']}/api/projects/{project_id}/"
    tasks_url = f"{ctx.obj['url']}/api/tasks?project={project_id}"
    headers = {
        "Authorization": ctx.obj['api_auth'],
        "Content-Type": "application/json"
    }

    console = Console()

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
            ("Completed Tasks: ", "bold red"), f"{project.get('num_tasks_with_annotations', 0)}\n",
            ("Total Annotations: ", "bold green"), f"{project.get('total_annotations_number', 0)}\n",
            ("Average Annotations: ", "bold magenta"), f"{project.get('avg_annotations_per_task', 0):.2f}"
        ),
        title=title,
        expand=True
    )

    # Fetch and display tasks
    tasks_response = requests.get(tasks_url, headers=headers)
    tasks_response.raise_for_status()
    tasks_data = tasks_response.json()

    tasks_table = Table(title="Tasks", show_header=True, header_style="bold magenta")
    tasks_table.add_column("ID", style="cyan", no_wrap=True)
    tasks_table.add_column("Page Number", style="magenta")
    tasks_table.add_column("Annotations", style="green")
    tasks_table.add_column("Status", style="blue")
    tasks_table.add_column("Contributors", style="yellow")

    if tasks_data:
        tasks = tasks_data.get('tasks', []) if isinstance(tasks_data, dict) else tasks_data

        if tasks:
            for task in tasks:
                if isinstance(task, dict):
                    task_id = str(task.get('id', 'N/A'))
                    data = task.get('data', {})
                    page_number = str(data.get('pageNumber', 'N/A'))
                    annotations_count = str(task.get('total_annotations', 0))
                    status = "Completed" if int(annotations_count) > 0 else "Pending"

                    # Fetch annotations for this task
                    annotations_url = f"{ctx.obj['url']}/api/tasks/{task_id}/annotations/"
                    annotations_response = requests.get(annotations_url, headers=headers)
                    annotations_response.raise_for_status()
                    annotations_data = annotations_response.json()

                    # Extract unique contributor emails
                    contributors = set()
                    for annotation in annotations_data:
                        if isinstance(annotation, dict) and 'completed_by' in annotation:
                            contributors.add(extract_email(annotation["created_username"]))

                    contributors_str = ", ".join(contributors) if contributors else "N/A"

                    tasks_table.add_row(task_id, page_number, annotations_count, status, contributors_str)
                else:
                    console.print(f"[bold yellow]Unexpected task format: {task}[/bold yellow]")
        else:
            tasks_table.add_row("N/A", "N/A", "N/A", "N/A", "N/A")
    else:
        tasks_table.add_row("N/A", "N/A", "N/A", "N/A", "N/A")

    # Display project details and tasks side by side
    columns = Columns([panel, tasks_table], equal=True, expand=True)
    console.print(columns)

    # Display summary
    summary = Table.grid(expand=True)
    summary.add_column(style="cyan", justify="right")
    summary.add_column(style="magenta")
    summary.add_row("Total Tasks:", str(project.get('task_number', 0)))
    summary.add_row("Completed Tasks:", str(project.get('num_tasks_with_annotations', 0)))
    summary.add_row("Completion Rate:", f"{project.get('num_tasks_with_annotations', 0) / project.get('task_number', 1) * 100:.2f}%")

    console.print(Panel(summary, title="Project Summary", expand=False))

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


def extract_email(input_string):
    # Define the email regex pattern
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    # Search for the first occurrence of an email
    match = re.search(email_pattern, input_string)
    if match:
        return match.group(0)
    else:
        return ''
