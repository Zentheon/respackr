# args.py

"""
Uses argparse to parse commandline arguments. Also sets up logging.
"""

# Revision of this module:
__version__ = "1.0.0"

# Default
import argparse
import logging

# Module imports
from modules.log import setup_logging

# Main class
class Args:
    def __init__(self, script_name, script_desc, script_ver):
        self.parser = argparse.ArgumentParser(
            prog = script_name,
            description = script_desc
        )
        self.add_arguments(script_name, script_ver)
        self.args = self.parser.parse_args()
        setup_logging(quiet=self.args.quiet, verbosity=self.args.verbose)
        logging.info("Test log")
        logging.verbose("Verbose log")
        logging.debug("File logging")

    def add_arguments(self, script_name, script_ver):
        self.parser.add_argument('--version', action='version', version=f'{script_name} {script_ver}')
        self.parser.add_argument('-v', '--verbose', action='count', default=0,
            help='Increase verbosity level (-v=INFO, -vv=VERBOSE, -vvv=DEBUG)')
        self.parser.add_argument('-q', '--quiet', action='store_true', help='Run without any feedback')
        self.parser.add_argument('-d', '--dry-run', action='store_true', help='Skip writing .zip archives to disk')
        self.parser.add_argument('--theme', type=str, help='Specify a theme to apply color mappings from (e.g., "--theme=nord")')
        self.parser.add_argument('--scale', type=int, help='Generate only for a specific scale (e.g., "--scale=3" for 72DPI)')
        self.parser.add_argument('--format', type=int, help='Generate only for a specific format key (e.g., "--format=6")')
        self.parser.add_argument('--packver', default='dev', type=str, help='Pack version string to use. Defaults to "dev"')

    def __getattr__(self, name):
        return getattr(self.args, name)

# Create an instance of Args to parse command line arguments
def create_args(script_name, script_desc, script_ver):
    return Args(script_name, script_desc, script_ver)
