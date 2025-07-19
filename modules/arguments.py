# args.py

"""
Uses argparse to parse commandline arguments. Also sets up logging.
"""

# Revision of this module:
__version__ = "1.1.0"

import argparse

# Allow args to be accessed globally
args = None

# Main class
class Args:
    def __init__(self, script_name, script_desc, script_ver):
        self.parser = argparse.ArgumentParser(
            prog = script_name,
            description = script_desc,
            formatter_class=argparse.RawTextHelpFormatter
        )
        self.add_arguments(script_name, script_ver)
        self.args = self.parser.parse_args()

    def add_arguments(self, script_name, script_ver):
        parse = self.parser.add_argument
        parse('--version', action='version', version=f'{script_name} {script_ver}',
            help='''Show the version number and exit.
            ''')
        parse('-v', '--verbose', action='count', default=0,
            help='Increase verbosity level (-v=VERBOSE, -vv=DEBUG, -vvv=TRACE)')
        parse('-q', '--quiet', action='store_true', help='Run without any feedback. Overrides "--verbose"')
        parse('-d', '--dry-run', action='store_true', help='Skip writing .zip archives to disk (test run)')
        parse('-e', '--exit-error', action='store_true', help='Makes non-critical errors trigger an exit')
        parse('--debug', action='store_true',
            help='''Adds extra formatting and error tracebacks to log messages
            ''')
        parse('--config-file', default='buildcfg.json', type=str, metavar='FILE',
            help='Configuration file to use. Defaults to "buildcfg.json"')
        parse('--theme', type=str, help='Specify a theme to apply color mappings from (e.g., "--theme nord")')
        parse('--scale', type=int, help='Generate only for a specific scale (e.g., "--scale 3" for 72DPI)')
        parse('--format', type=int, help='Generate only for a specific format key (e.g., "--format 6")')
        parse('--packver', default='dev', type=str, help='Pack version string to use. (Default: "dev")')

    def __getattr__(self, name):
        return getattr(self.args, name)

# Create an instance of Args to parse command line arguments
def create_args(script_name, script_desc, script_ver):
    global args
    args = Args(script_name, script_desc, script_ver)
