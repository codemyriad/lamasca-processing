import click

@click.group()
def cli():
    """MyProject CLI tool."""
    pass

@cli.command()
def hello():
    """Simple command that says hello."""
    click.echo("Hello from myproject!")

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
def process_dir(directory):
    """Process a directory of images."""
    click.echo(f"Processing directory: {directory}")
    # TODO: Implement directory processing logic

if __name__ == '__main__':
    cli()
