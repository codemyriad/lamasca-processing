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

@projects.command(name="list")
@click.pass_context
def list_projects(ctx):
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
        tasks_data = tasks_response.json()

        # Example task_data:
        """
        {'total_annotations': 4, 'total_predictions': 0, 'total': 20, 'tasks': [{'id': 229, 'drafts': [], 'annotators': [], 'inner_id': 1, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_01.jpeg', 'pageNumber': 1, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.542420Z', 'updated_at': '2024-10-11T14:01:49.542451Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 230, 'drafts': [], 'annotators': [], 'inner_id': 2, 'cancelled_annotations': 0, 'total_annotations': 1, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [{'user_id': 2}], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_02.jpeg', 'pageNumber': 2, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.542503Z', 'updated_at': '2024-10-11T17:58:39.133002Z', 'is_labeled': True, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 231, 'drafts': [], 'annotators': [], 'inner_id': 3, 'cancelled_annotations': 0, 'total_annotations': 1, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [{'user_id': 2}], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_03.jpeg', 'pageNumber': 3, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.542553Z', 'updated_at': '2024-10-11T18:18:01.054404Z', 'is_labeled': True, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 232, 'drafts': [], 'annotators': [], 'inner_id': 4, 'cancelled_annotations': 0, 'total_annotations': 1, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [{'user_id': 2}], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_04.jpeg', 'pageNumber': 4, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.542632Z', 'updated_at': '2024-10-11T18:16:33.889726Z', 'is_labeled': True, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 233, 'drafts': [], 'annotators': [], 'inner_id': 5, 'cancelled_annotations': 0, 'total_annotations': 1, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [{'user_id': 2}], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_05.jpeg', 'pageNumber': 5, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.542680Z', 'updated_at': '2024-10-11T18:31:49.899539Z', 'is_labeled': True, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 234, 'drafts': [], 'annotators': [], 'inner_id': 6, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_06.jpeg', 'pageNumber': 6, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.542726Z', 'updated_at': '2024-10-11T14:01:49.542735Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 235, 'drafts': [], 'annotators': [], 'inner_id': 7, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_07.jpeg', 'pageNumber': 7, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.542772Z', 'updated_at': '2024-10-11T14:01:49.542781Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 236, 'drafts': [], 'annotators': [], 'inner_id': 8, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_08.jpeg', 'pageNumber': 8, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.542817Z', 'updated_at': '2024-10-11T14:01:49.542826Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 237, 'drafts': [], 'annotators': [], 'inner_id': 9, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_09.jpeg', 'pageNumber': 9, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.542864Z', 'updated_at': '2024-10-11T14:01:49.542877Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 238, 'drafts': [], 'annotators': [], 'inner_id': 10, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_10.jpeg', 'pageNumber': 10, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.542935Z', 'updated_at': '2024-10-11T14:01:49.542946Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 239, 'drafts': [], 'annotators': [], 'inner_id': 11, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_11.jpeg', 'pageNumber': 11, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.542985Z', 'updated_at': '2024-10-11T14:01:49.542995Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 240, 'drafts': [], 'annotators': [], 'inner_id': 12, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_12.jpeg', 'pageNumber': 12, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.543033Z', 'updated_at': '2024-10-11T14:01:49.543043Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 241, 'drafts': [], 'annotators': [], 'inner_id': 13, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_13.jpeg', 'pageNumber': 13, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.543080Z', 'updated_at': '2024-10-11T14:01:49.543090Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 242, 'drafts': [], 'annotators': [], 'inner_id': 14, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_14.jpeg', 'pageNumber': 14, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.543128Z', 'updated_at': '2024-10-11T14:01:49.543137Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 243, 'drafts': [], 'annotators': [], 'inner_id': 15, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_15.jpeg', 'pageNumber': 15, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.543174Z', 'updated_at': '2024-10-11T14:01:49.543183Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 244, 'drafts': [], 'annotators': [], 'inner_id': 16, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_16.jpeg', 'pageNumber': 16, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.543221Z', 'updated_at': '2024-10-11T14:01:49.543231Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 245, 'drafts': [], 'annotators': [], 'inner_id': 17, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_17.jpeg', 'pageNumber': 17, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.543289Z', 'updated_at': '2024-10-11T14:01:49.543299Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 246, 'drafts': [], 'annotators': [], 'inner_id': 18, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_18.jpeg', 'pageNumber': 18, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.543340Z', 'updated_at': '2024-10-11T14:01:49.543350Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 247, 'drafts': [], 'annotators': [], 'inner_id': 19, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_19.jpeg', 'pageNumber': 19, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.543388Z', 'updated_at': '2024-10-11T14:01:49.543397Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}, {'id': 248, 'drafts': [], 'annotators': [], 'inner_id': 20, 'cancelled_annotations': 0, 'total_annotations': 0, 'total_predictions': 0, 'annotations_results': '', 'predictions_results': '', 'file_upload': None, 'storage_filename': None, 'annotations_ids': '', 'predictions_model_versions': '', 'updated_by': [], 'data': {'ocr': 'https://eu2.contabostorage.com/55b89d240dba4119bef0d60e8402458a:newspapers/lamasca-pages/1994/lamasca-1994-12-21/page_20.jpeg', 'pageNumber': 20, 'date': '1994-12-21'}, 'meta': {}, 'created_at': '2024-10-11T14:01:49.543434Z', 'updated_at': '2024-10-11T14:01:49.543444Z', 'is_labeled': False, 'overlap': 1, 'comment_count': 0, 'unresolved_comment_count': 0, 'last_comment_updated_at': None, 'project': 18, 'comment_authors': []}]}

        """

        # TODO: extract tasks from task data

        if tasks:
            tasks_table = Table(title="Tasks")
            tasks_table.add_column("ID", style="cyan")
            tasks_table.add_column("Data", style="magenta")
            tasks_table.add_column("Annotations", style="green")

            for task in tasks:
                if isinstance(task, dict):
                    tasks_table.add_row(
                        str(task.get('id', 'N/A')),
                        str(task.get('data', {})),
                        str(len(task.get('annotations', [])))
                    )
                else:
                    console.print(f"[bold yellow]Unexpected task format: {task}[/bold yellow]")

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
