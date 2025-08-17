# respackr/__init__.py

__description__ = "Easily create resourcepacks for multiple Minecraft: Java Edition versions."
__version__ = "3.0.0"
__authors__ = ["Zentheon <zentheon@mailbox.org>"]
__license__ = "GPL-3.0"

import click

from respackr.logger import LogWrapper

SPEC_FILE = "respackr/spec.toml"

# Initialize logging
log = LogWrapper("respackr_log")


# cli group and global opts
@click.group(epilog="Try 'respackr help COMMAND' to get more info about a specific command.")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity level (-v=DEBUG, -vv=VOMIT).",
)
@click.option(
    "-q",
    "--quiet",
    count=True,
    help="Run with less feedback (-q=MINIMAL, -qq=NOTHING).",
)
@click.option(
    "-d",
    "--debug-filter",
    type=str,
    multiple=True,
    help="Sets log level to DEBUG and adds extra ouput based on category.",
)
@click.option(
    "--config-file",
    default="respackr.toml",
    metavar="PATH",
    help="Specify a different path to a config file.",
)
def cli(**clargs):
    """Main commandline interface group that gathers basic args and configures logging."""
    current_loglevel = "info"
    debug_filter = []

    global glargs
    glargs = clargs

    # Calculate log settings from clargs
    if clargs["verbose"] == 0:
        current_loglevel = "info"
    elif clargs["verbose"] == 1:
        current_loglevel = "debug"
    else:
        debug_filter = ["all"]

    for filter in clargs["debug_filter"]:
        debug_filter.append(filter)

    if debug_filter:
        current_loglevel = "debug"

    if clargs["quiet"] == 1:
        current_loglevel = "warning"
    if clargs["quiet"] >= 1:
        current_loglevel = "critical"

    log.settings(log.name, current_loglevel, debug_filter, False)


def main():
    from respackr.generate import generate
    from respackr.info import ascii, help, info

    ascii = ascii
    generate = generate
    help = help
    info = info

    cli()
