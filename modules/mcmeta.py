# mcmeta.py

# Revision of this module:
__version__ = "1.0.0"

import logging as log
import json

from modules.arguments import args
from modules.config import config
from modules.stats import svg_talley
from modules.error import record_warn, record_err, record_crit

def generate_pack_mcmeta(current_format, scale, src_files):
    """
    Generates the pack.mcmeta file and adds it to src_files.
    Args:
        current_format (int): The current format key.
        config.sorted_formats (dict): Dictionary of all available config.sorted_formats.
        description (str): Base description for the pack.
        scale (int): The current scale being processed.
        src_files (dict): The dictionary of files to be included in the ZIP.
    """
    # Check for and remove previous pack.mcmeta
    pack_mcmeta_path = "pack.mcmeta"
    if pack_mcmeta_path in src_files:
        del src_files[pack_mcmeta_path]
        log.debug(f"  Removed existing {pack_mcmeta_path}")

    # Bump format to 1 if it's 0
    # "Format 0" packs are created due to a change in the
    # enchanting table UI in 1.7 without a format change.
    if current_format == 0:
      current_format = 1

    # Determine supported_formats range
    min_supported_format = current_format
    for key in config.sorted_formats.keys():
        if key < current_format:
            min_supported_format = key + 1
            break

    supported_formats_str = f"{min_supported_format}, {current_format}"

    # If scale is None (svg processing disabled), don't add a scale suffix
    def check_scale(scale):
        if scale is None:
            return ""
        else:
            return f" (Scale {scale})"

    # Create pack.mcmeta content
    pack_data = {
        "pack": {
            "pack_format": current_format,
            "supported_formats": [supported_formats_str],
            "description": f"{config.description}{check_scale(scale)}"
        }
    }
    # Convert to JSON string and then to bytes
    pack_mcmeta_content = json.dumps(pack_data, indent=4).encode('utf-8')
    # Add to src_files
    src_files[pack_mcmeta_path] = pack_mcmeta_content
    log.verbose(f"  Generated new {pack_mcmeta_path} with pack_format {current_format} and description '{config.description}{check_scale(scale)}")
