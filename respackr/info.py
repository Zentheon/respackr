# respackr/info.py

"""Miscelaneous info-related subcommands."""

import click
from termaconfig import ConfigValidationError, TermaConfig
from terminaltables3 import DoubleTable

from respackr import SPEC_FILE, cli
from respackr.ascii import assemble_logo


# Alternate help command
# Blank string seems to disable the help argument entirely
@cli.command(context_settings={"help_option_names": ""})
@click.argument("command_name", metavar="COMMAND", required=False)
def help(command_name):
    """Get the help message for any command."""

    if not command_name:
        with click.Context(cli) as ctx:
            click.echo(cli.get_help(ctx))
            exit()

    if command_name not in cli.commands:
        raise click.UsageError(f"The command '{command_name}' doesn't exist.")

    if command_name == "help":
        with click.Context(cli) as ctx:
            click.echo(cli.get_help(ctx))
            exit()

    command = cli.commands[command_name]
    with click.Context(command) as ctx:
        lines = command.get_help(ctx).splitlines()
        lines[0] = f"Usage: respackr [GENERIC OPTIONS] {command.name} [OPTIONS]"
        click.echo("\n".join(lines))
        exit()


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
