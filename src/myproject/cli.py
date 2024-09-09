import click

@click.command()
def hello():
    """Simple command that says hello."""
    click.echo("Hello, World!")

if __name__ == '__main__':
    hello()
