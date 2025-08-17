# respackr/info.py

"""Miscelaneous info-related subcommands."""

import click
from termaconfig import ConfigValidationError, TermaConfig
from terminaltables3 import DoubleTable

from respackr import SPEC_FILE, cli
from respackr.ascii import assemble_logo


@cli.command()
def ascii():
    """Simply prints out the fun ascii-ified logo and version number."""
    logo_lines = assemble_logo()
    click.echo()
    for line in logo_lines:
        click.echo(line)


@cli.command()
def info():
    """Loads the provided config file and displays the results."""
    # Load global args after cli has been initialized
    from respackr import glargs

    logo_lines = assemble_logo()
    click.echo()
    for line in logo_lines:
        click.echo(line)

    config_file = glargs["config_file"]

    global config

    try:
        config = TermaConfig(config_file, SPEC_FILE, tabletype=DoubleTable, logging=False)
    except ConfigValidationError:
        click.echo()
        click.echo("Config failed validation. Please review any errors.")
