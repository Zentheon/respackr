# exclusion.py

# Revision of this module:
__version__ = "1.0.0"

import logging as log
import json

from modules.arguments import args
from modules.config import config
from modules.stats import svg_talley
from modules.error import record_warn, record_err, record_crit

def apply_exclusions(current_format, src_files, gen_images):
    """
    Applies exclusion rules to both source files and generated images.
    Handles both file and directory paths.

    Args:
        current_format: The format key being processed
        config.source_dir: Source directory path
        src_files: Dictionary of original files
        gen_images: Dictionary of generated PNGs by DPI

    Returns:
        Tuple of (modified_src_files, modified_gen_images)
    """

    # Check for and load exlusion file from src_files
    if f"{current_format}.json" in src_files:
        log.verbose(f"  Found exclusion list: {current_format}.json")
        file_data = src_files[f"{current_format}.json"].decode('UTF8')
        exclusion_data = json.loads(file_data)
        # Normalize excluded paths
        excluded_paths = [p.replace('\\', '/').rstrip('/') for p in exclusion_data.get('exclusions')]
    else:
        log.verbose(f"  {current_format}.json not found, skipping exclusions")
        return src_files, gen_images

    try:
        for rel_path in list(src_files.keys()):
            normalized_rel_path = rel_path.replace('\\', '/').rstrip('/')

            # Check if path matches any exclusion file or directory
            for excluded_path in excluded_paths:
                if (normalized_rel_path == excluded_path or
                    normalized_rel_path.startswith(f"{excluded_path}/")):
                    if rel_path in src_files:
                        log.debug(f"    Excluding file: {rel_path}")
                        del src_files[rel_path]
                    else:
                        log.debug(f"    Skipped nonpresent entry in src_files: {rel_path}")

        # Process generated PNGs across all DPI variants
        for dpi, png_files in list(gen_images.items()):
            for rel_path in list(png_files.keys()):
                # Normalize excluded paths
                normalized_rel_path = rel_path.replace('\\', '/').rstrip('/')

                # Check PNG paths against exclusions
                for excluded_path in excluded_paths:
                    png_path = excluded_path[:-4] + '.png' if excluded_path.endswith('.svg') else excluded_path
                    png_path = png_path.rstrip('/')

                    if (normalized_rel_path == png_path or
                        normalized_rel_path.startswith(f"{png_path}/")):
                        if rel_path in png_files:
                            log.debug(f"    Excluding generated PNG: {rel_path} (DPI {dpi})")
                            del png_files[rel_path]
                        else:
                            log.debug(f"    Skipped nonpresent entry in gen_images: {rel_path}")

    except Exception as e:
        record_err(61, "exclusion_error", f"Error applying exclusions: {str(e)}")

    return src_files, gen_images
