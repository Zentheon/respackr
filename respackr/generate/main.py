# respackr/generate/main.py

import click
from termaconfig import ConfigValidationError, TermaConfig
from terminaltables3 import DoubleTable

from respackr import cli


@cli.command()
@click.option(
    "--config-file",
    default="respackr.toml",
    metavar="PATH",
    help="Specify a different path to a config file.",
)
@click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    help="Skip writing .zip archives to disk (test run).",
)
@click.option(
    "-e",
    "--exit-error",
    is_flag=True,
    help="Quit generation on any error, not just critical ones.",
)
@click.option(
    "--packver",
    default="dev",
    type=str,
    metavar="VERSION",
    help='Pack version string to use. (Default: "dev")',
)
@click.option(
    "-t",
    "--theme",
    type=str,
    metavar="THEME",
    help='Specify themes to search for and create (e.g., "--theme nord").',
)
@click.option(
    "-s",
    "--scale",
    type=int,
    multiple=True,
    help='Generate only specific resolutions (e.g., "-s 2 -s 3").',
)
def generate(**clargs):
    """Generates zipped resourcepacks, ready to publish or use in-game"""

    spec_path = "respackr/spec.toml"

    print(clargs)
    config_file = clargs["config_file"]

    global config

    try:
        config = TermaConfig(config_file, spec_path, tabletype=DoubleTable, logging=False)
    except ConfigValidationError:
        print()
        print("Errors are present in configuration. Exiting...")
        exit()

    print("Testing config:", config["pack"])
