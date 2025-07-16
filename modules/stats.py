# stats.py

"""
Handles statistics variables and printouts
"""

# Revision of this module:
__version__ = "1.0.0"

# Regular imports
from collections import defaultdict

# Initialize statistics tracking variables
# general int counters
talley = {
    'formats_processed': 0,
    'archives_created': 0,
    'source_files_loaded': 0,
}

# SVG processing-specific
svg_talley = {
    'theme_color_edits': defaultdict(int),
    'svg_files_edited': 0,
    'png_files_generated': 0,
}

# Files loaded from load_src by extension
file_extensions = defaultdict(int)

# Types of problem codes
codes = {
    'warning': defaultdict(int),
    'error': defaultdict(int),
    'critical': defaultdict(int)
}


def print_summary():
    """
    Returns a nice printout of values collected in above variables
    """

    print("\n======= SUMMARY =======")

    print("\nTalley:")
    print(f"- Total files loaded: {talley['source_files_loaded']}")
    print(f"- Formats processed: {talley['formats_processed']}")
    print(f"- Resourcepack ZIPs written: {talley['archives_created']}")

    print("\nLoaded Filetypes:")
    for filetype, amount in sorted(file_extensions.items(), key=lambda item: item[1], reverse=True):
        print(f"- {filetype.lstrip('.')} ({amount})")

    # SVG editing-specific
    if svg_talley['png_files_generated']:
        print("\nSVG Talley:")
        print(f"- SVG files themed: {svg_talley['svg_files_edited']}")
        print(f"- PNG files generated: {svg_talley['png_files_generated']}")

    if svg_talley['theme_color_edits']:
        print("\nColors applied to SVG objects:")
        for color, amount in sorted(svg_talley['theme_color_edits'].items(), key=lambda item: item[1], reverse=True):
            print(f"- {color.lstrip('.')}: {amount}")

    print("\nWarnings:")
    if codes['warning']:
        for warning, count in sorted(codes['warning'].items()):
            print(f"- {warning}: {count}")
    else:
        print("- No warnings recorded")

    print("\nErrors:")
    if codes['error']:
        for error, count in sorted(codes['error'].items()):
            print(f"- {error}: {count}")
    else:
        print("- No errors recorded")
    print("========================")
