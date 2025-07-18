# exclusion.py

# Revision of this module:
__version__ = "2.0.0"

import logging as log
import json

from modules.arguments import args
from modules.config import config
from modules.error import record_warn, record_err, record_crit

# Open pack.mcmeta as regular text file to fill placeholders first
def load_mcmeta(template_path, src_files, placeholders):

    if not template_path in src_files:
        record_crit(81, "mcmeta_not_found", f"{template_path} template file was not found")
        return None

    try:
        template_data = src_files[template_path].decode('utf-8') \
            if isinstance(src_files[template_path], bytes) \
            else src_files[template_path]
        # Log filedata to debug
        log.debug("    Found pack.mcmeta template:")
        for line in template_data.splitlines():
            log.debug(f"    {line}")

        # Replace placeholders with actual values
        mcmeta_data = template_data
        for placeholder, value in placeholders.items():
            log.trace(f"    replacing: {placeholder}: {value}")
            mcmeta_data = mcmeta_data.replace(placeholder, str(value))

        return mcmeta_data

    except Exception as e:
        record_crit(82, "mcmeta_load_error", f"Error loading mcmeta template: {e}")
        return None

def get_min_fmt(cur_fmt):
    min_fmt = cur_fmt
    # Get next lowest format, if it exists, and add 1
    for fmt in config.sorted_formats.keys():
        if fmt < cur_fmt:
            min_fmt = fmt + 1
            log.trace(f"    Found lower format: {fmt} + 1 -> {min_fmt}")
            break

    return min_fmt

def get_max_fmt(cur_fmt):
    max_fmt = cur_fmt
    # Check if cur_fmt is the first (highest) entry
    first_fmt = next(iter(config.sorted_formats))
    log.trace(f"    first_fmt: {first_fmt}")
    if cur_fmt == first_fmt:
        # Only set a higher format if the config specifies
        if config.max_format:
            max_fmt = cur_fmt + config.max_format
        log.trace(f"    cur_fmt is latest: {cur_fmt} + {config.max_format} -> {max_fmt}")

    return max_fmt

def generate_pack_mcmeta(cur_fmt, cur_scale, src_files):
    """
    Generates the pack.mcmeta file and adds it to src_files.
    Args:
        cur_fmt (int): The current format key.
        description (str): Base description for the pack.
        current_cur_scale (int): The current cur_scale being processed.
        src_files (dict): The dictionary of files to be included in the ZIP.
    """
    log.debug("  Creating new pack.mcmeta file...")
    # Initial variables
    # Bump format to 1 if it's 0
    # "Format 0" packs are created due to a change in the
    # enchanting table UI in 1.7 without a format change.
    if cur_fmt == 0: cur_fmt = 1
    mcmeta_path = "pack.mcmeta"
    template_path = "pack.json"
    placeholders = {
        "{format}": cur_fmt,
        # min_fmt should be the next lowest fmt + 1
        "{min_format}": get_min_fmt(cur_fmt),
        # max_fmt should have a pre-defined value to it if there are
        # no higher values in sorted_formats, ie removing the warning
        # from however many future unreleased MC versions.
        "{max_format}": get_max_fmt(cur_fmt),
        "{versions}": config.sorted_formats[cur_fmt],
        "{scale}": cur_scale
    }

    # Check for and remove previous pack.mcmeta
    if mcmeta_path in src_files:
        del src_files[mcmeta_path]
        log.debug(f"    Removed existing {mcmeta_path}")

    # Perform initial file validations and fill placeholders
    mcmeta_data = load_mcmeta(template_path, src_files, placeholders)

    # Check json validity
    try:
        log.trace("    Loading mcmeta_data as json before dumping")
        mcmeta_data = json.loads(mcmeta_data)
        mcmeta_data = json.dumps(mcmeta_data, indent=2)
    except Exception as err:
        record_crit(85, "mcmeta_json_error", f"Loading {template_path} as json failed: {err}")

    # Add output to src_files
    src_files[mcmeta_path] = mcmeta_data

    log.debug("    Output pack.mcmeta file:")
    for line in mcmeta_data.splitlines():
        log.debug(f"    {line}")
    log.verbose(f"  Generated new {mcmeta_path}")

    return src_files
