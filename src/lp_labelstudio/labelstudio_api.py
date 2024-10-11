import click
import os

@click.group()
@click.option('--url', required=True, envvar='LABELSTUDIO_URL', help='Label Studio API URL')
@click.option('--api-key', required=True, envvar='LABELSTUDIO_API_KEY', help='Label Studio API Key')
@click.pass_context
def labelstudio_api(ctx, url, api_key):
    """Command group for Label Studio API operations."""
    ctx.ensure_object(dict)
    ctx.obj['url'] = url
    ctx.obj['api_key'] = api_key

# Add subcommands here as needed
