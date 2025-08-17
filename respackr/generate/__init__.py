# respackr/generate/__init__.py

import click
from termaconfig import ConfigValidationError, TermaConfig
from terminaltables3 import DoubleTable

from respackr import SPEC_FILE, ascii, cli
from respackr.generate import sources


@cli.command()
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
    # Load global args after cli has been initialized
    from respackr import glargs

    logo_lines = ascii.assemble_logo()
    click.echo()
    for line in logo_lines:
        click.echo(line)

    config_file = glargs["config_file"]

    global config

    try:
        config = TermaConfig(config_file, SPEC_FILE, tabletype=DoubleTable, logging=False)
    except ConfigValidationError:
        print()
        print("Errors are present in configuration. Exiting...")
        exit()

    print("Testing config:", config["pack"])
    print(clargs)

    src_files = sources.SourceLoader(str(config["pack"]["source_path"]))
    src_files.load_sources()
    print(src_files["2.json"])
    print("Filetypes:", src_files.filetypes)
