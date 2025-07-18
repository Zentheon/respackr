# theme.py

# Revision of this module:
__version__ = "1.0.0"

import os
import json
import logging as log

from modules.arguments import args
from modules.config import config
from modules.stats import svg_talley
from modules.error import record_warn, record_err, record_crit

def apply_theme(src_files):
    """
    Replaces colors in SVG content based on a theme's color map JSON file and default colors as search keys.
    Iterates through src_files and modifies SVG content in place.
    Args:
        src_files (dict): The dictionary of source files.
    Returns:
        dict: Modified src_files dictionary with themed SVG content.
    """

    log.trace("  Called apply_theme")
    if not args.theme:
        log.verbose(f"  Skipping theme edits (no theme specified)")
        return src_files

    if not os.path.isdir(config.theme_dir):
        record_crit(31, "theme_dir_not_found", f"Theme directory: '{config.theme_dir}' is not valid.")
        return src_files

    theme_file = os.path.join(config.theme_dir, f"{args.theme}.json")
    if not os.path.exists(theme_file):
        record_crit(32, "theme_file_not_found", f"Theme file not found: {theme_file}")
        return src_files

    try:
        with open(theme_file, 'r') as file:
            theme_data = json.load(file)
            theme_dump = json.dumps(theme_data, indent=2)
            log.debug("    Loaded theme data:")
            for line in theme_dump.splitlines():
                log.debug(f"    {line}")
            theme_color_map = theme_data.get('colors', {})

        log.verbose(f"  Editing with theme '{args.theme}':")
        for rel_path in list(src_files.keys()):
            if rel_path.lower().endswith('.svg'):
                log.debug(f"    Applying theme to SVG: {rel_path}")
                svg_content = src_files[rel_path].decode('utf-8') if isinstance(src_files[rel_path], bytes) else src_files[rel_path]
                if svg_content is None:
                    record_err(35, "svg_load_error", f"Could not load SVG content for {rel_path}")
                    continue

                new_color_map = {}
                try:
                    if config.color_map:
                        for default_color_key, default_hex_color in config.color_map.items():
                            if default_color_key in theme_color_map and default_hex_color in svg_content:
                                color_count = svg_content.count(default_hex_color)

                                # Stat logging
                                svg_talley['svg_files_edited'] += 1
                                color_stat = f"{default_color_key} ({default_hex_color} -> {theme_color_map[default_color_key]})"
                                svg_talley['theme_color_edits'][color_stat] += color_count

                                new_color_map[default_hex_color.lower()] = theme_color_map[default_color_key].lower()
                                log.trace(f"      Mapping {color_count} instances of color '{default_color_key}': "
                                    f"'{default_hex_color}' -> '{theme_color_map[default_color_key]}'")
                            else:
                                new_color_map[default_hex_color.lower()] = default_hex_color.lower()
                                log.trace(f"      No theme color for '{default_color_key}', "
                                    f"keeping default '{default_hex_color}'")

                    # Apply all color replacements
                    themed_svg = svg_content
                    log.trace("      Triggering color replacements")
                    for original_color, new_color in new_color_map.items():
                        themed_svg = themed_svg.replace(original_color, new_color)

                    src_files[rel_path] = themed_svg.encode('utf-8') # Update src_files with themed SVG content
                except Exception as err:
                    record_crit(36, "svg_theming_error", f"Error theming file: '{args.theme}': {str(err)}",
                        f"⤷ Path: {rel_path}")

    except Exception as err:
        record_crit(33, "theme_processing_error", f"Error processing theme '{args.theme}': {str(err)}")

    return src_files
