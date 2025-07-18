# svg2png.py

# Revision of this module:
__version__ = "1.0.1"

import logging as log
from collections import defaultdict
from xml.etree import ElementTree as ET

from modules.arguments import args
from modules.config import config
from modules.stats import svg_talley
from modules.error import record_warn, record_err, record_crit

def convert_svg_to_png(src_files):
    """
    Convert SVG content to PNG with resolution fetching and scaling.

    For whatever reason, the `dpi` parameter for CarioSVG does not work in Python,
    so we have to figure out the target width x height ourselves.

    Args:
        src_files (dict): Dictionary of source files, including SVG content.
    Returns:
        defaultdict: A dictionary of generated PNGs, keyed by DPI.
    """

    # Import CarioSVG now, since it's needed
    from cairosvg import svg2png

    log.trace("Called convert_svg_to_png")
    gen_images = defaultdict(dict)

    scales = config.sorted_scales
    # Check args.scale and limit scales to only the provided one
    if args.scale:
        if args.scale in config.sorted_scales:
            scales = {k: v for k, v in config.sorted_scales.items() if k == args.scale}
            log.debug(f"  Limiting image gen. to scale {args.scale} ({scales})")
        else:
            record_crit(44, "scale_not_valid", f"Provided scale: {args.scale} is not present in config.")

    # Iterate over a copy of keys because we'll be modifying src_files
    for rel_path in list(src_files.keys()):
        if rel_path.lower().endswith('.svg'):
            log.debug(f"  Creating image(s) for SVG: {rel_path}")

            try:
                # Load content from `src_files` (already themed if theme was applied)
                svg_content = src_files[rel_path].decode('utf-8') if isinstance(src_files[rel_path], bytes) \
                    else src_files[rel_path]

                if svg_content is None:
                    record_err(42, "svg_load_error", f"Could not load SVG content for {rel_path}")
                    continue

                # Generate images for each DPI in the filtered list
                for scale, dpi in scales.items():
                    log.trace(f"    Converting to PNG at target DPI {dpi}...")

                    # Parse SVG to get original dimensions
                    root = ET.fromstring(svg_content)
                    try:
                        width_attr = root.get('width')
                        height_attr = root.get('height')
                        width = float(width_attr[:-2]) if width_attr.endswith('pt') else float(width_attr)
                        height = float(height_attr[:-2]) if height_attr.endswith('pt') else float(height_attr)
                    except (ValueError, TypeError) as err:
                        width, height = 1024, 1024
                        record_err(43, "svg_bad_dimensions", f"Falling back to 1024x1024: {str(err)}",
                            f"⤷ At: {rel_path}")

                    scale_factor = dpi / 96.0
                    target_width = int(width * scale_factor)
                    target_height = int(height * scale_factor)

                    log.trace(f"    Original dimensions: {width}x{height}pt")
                    log.trace(f"    Target dimensions: {target_width}x{target_height}px")

                    png_data = svg2png(
                        bytestring=svg_content,
                        output_width=target_width,
                        output_height=target_height,
                        dpi=dpi,
                        scale=1.0,
                        unsafe=False
                    )

                    if not png_data:
                        record_err(43, "no_png_data", f"Empty PNG data returned for {rel_path}")

                    # Store in gen_images dictionary
                    gen_images[dpi][f"{rel_path[:-4]}.png"] = png_data
                    svg_talley['png_files_generated'] += 1
                    log.trace(f"    Created PNG for Scale {scale} ({dpi} DPI): {rel_path[:-4]}.png")

                # Remove the SVG entry from src_files as it is no longer needed
                del src_files[rel_path]

            except Exception as e:
                record_err(41, "svg_processing_error", f"Error creating image for SVG: {str(e)}", f"⤷ At: {rel_path}")

    log.verbose("")
    log.verbose(f"Total images created: {svg_talley['png_files_generated']}")
    return gen_images
