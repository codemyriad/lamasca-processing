import os
import click
from typing import List

def generate_index_txt(directories: List[str], replace_from: str, replace_to: str) -> None:
    for directory in directories:
        jpeg_files = [f for f in os.listdir(directory) if f.lower().endswith('.jpeg')]

        index_content = []
        for jpeg_file in jpeg_files:
            full_path = os.path.join(directory, jpeg_file)
            url = full_path.replace(replace_from, replace_to)
            index_content.append(url)

        index_file_path = os.path.join(directory, 'index.txt')
        with open(index_file_path, 'w') as f:
            f.write('\n'.join(index_content))

        click.echo(f"Created index.txt in {directory} with {len(index_content)} URLs")

@click.command()
@click.option('--replace-from', required=True, help='The path prefix to replace')
@click.option('--replace-to', required=True, help='The URL prefix to replace with')
@click.argument('directories', nargs=-1, type=click.Path(exists=True, file_okay=False, dir_okay=True))
def cli_generate_index_txt(directories: List[str], replace_from: str, replace_to: str) -> None:
    """Generate index.txt files containing full URLs of JPEG files in the given directories."""
    generate_index_txt(directories, replace_from, replace_to)

if __name__ == '__main__':
    cli_generate_index_txt()
