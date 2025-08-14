# respackr/__init__.py

__description__ = "Easily create resourcepacks for multiple Minecraft: Java Edition versions."
__version__ = "3.0.0"
__authors__ = ["Zentheon <zentheon@mailbox.org>"]
__license__ = "GPL-3.0"

import logging as log

import click

log.basicConfig(
    level=log.INFO,
    format="%(asctime)s:%(name)s:%(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


@click.group(epilog="Try 'respackr help COMMAND' for get info more about a specific command.")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity level (-v=VERBOSE, -vv=DEBUG, -vvv=TRACE).",
)
@click.option(
    "-q",
    "--quiet",
    count=True,
    help="Run with less feedback (-q=MINIMAL, -qq=NOTHING).",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Adds extra formatting and error tracebacks to log messages.",
)
def cli(**clargs):
    pass


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


def main():
    from respackr.generate.main import generate

    generate = generate

    cli()
