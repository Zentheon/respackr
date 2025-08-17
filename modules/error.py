# log.py

"""
Errors and warnings are kept in a talley for the end summary.

Exit code contexts:
    4-10: Problems with configuration file
    11-20: Source scan problems
    21-30: Incorrect flag values
    31-40: SVG theming-specific
    41-50: SVG-to-PNG conversion-specific
    51-60: ZIP creation-specific
    61-70: Exclusion-specific
    71-80: Inclusion-specific
    81-90: pack.mcmeta-specific
"""

# Revision of this module:
__version__ = "1.1.1"

import logging as log
import sys
import traceback

from modules.arguments import args
from modules.stats import codes


def handle_log(header, err_type, messages):
    # Add stacktrace if debug flag is set
    if args.debug:
        if sys.exc_info()[2]:
            tb = traceback.format_exc()
            # Logging individual lines looks nicer
            for line in tb.splitlines():
                log.error(line)

        log.error(f"{header} ({err_type}): {messages[0]}")
        # Each extra message gets its own line
        for message in messages[1:]:
            log.error(message)

        log.error("")  # Spacer
    else:
        log.error(f"Error ({err_type}): {messages[0]}")
        for message in messages[1:]:
            log.error(message)


def record_warn(warn_type, *messages):
    codes["warning"][warn_type] += 1
    handle_log("Warning", warn_type, messages)


def record_err(code, err_type, *messages):
    codes["error"][err_type] += 1
    handle_log("Error", err_type, messages)
    # Check exit_error flag
    if args.exit_error:
        log.trace("exit_error was set, triggering exit")
        exit(code)


def record_crit(code, crit_type, *messages):
    codes["critical"][crit_type] += 1
    handle_log("Fatal", crit_type, messages)
    exit(code)
