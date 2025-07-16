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
"""

# Revision of this module:
__version__ = "1.0.0"

import logging as log
from modules.stats import codes
from modules.arguments import get_args

def record_warn(warn_type, message):
    codes['warning'][warn_type] += 1
    log.warning(f"Warning ({warn_type}): {message}")

def record_err(code, err_type, message):
    codes['error'][err_type] += 1
    log.error(f"Error ({err_type}): {message}")
    # Check exit_error flag
    if get_args().exit_error:
        exit(code)

def record_crit(code, crit_type, message):
    codes['critical'][crit_type] += 1
    log.critical(f"Fatal ({crit_type}): {message}")
    exit(code)
