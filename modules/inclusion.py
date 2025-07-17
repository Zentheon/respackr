# inclusion.py

# Revision of this module:
__version__ = "1.0.0"

import logging as log
import json

from modules.arguments import args
from modules.config import config
from modules.stats import svg_talley
from modules.error import record_warn, record_err, record_crit

def apply_inclusions(current_format, src_files, gen_images):
    """
    Merges assets from format-specific directories into root source directory.

    Args:
        current_format (int): The current format key being processed.
        src_files (dict): Dictionary of original files.
        gen_images (defaultdict): Dictionary of generated PNGs by DPI.

    Returns:
        Tuple of (modified_src_files, modified_gen_images)
    """

    # Function to match gen_images inclusions
    def gen_images_filter(gen_images, inclusion_dir):
        filtered_img = {}
        for dpi, value in gen_images.items():
            if isinstance(value, dict):
                sub_matches = {k: v for k, v in value.items() if k.startswith(str(inclusion_dir))}
                if sub_matches:  # Only add if there are matches
                    filtered_img[dpi] = sub_matches

        return filtered_img

    # Initial dictionaries
    inclusion_dir = f"{current_format}/"
    filtered_src = {k: v for k, v in src_files.items() if k.startswith(inclusion_dir)}
    filtered_img = gen_images_filter(gen_images, inclusion_dir)

    # Check if any entries were found
    if filtered_src or filtered_img:
        log.verbose(f"  Merging format inclusion folder: {inclusion_dir}")
    else:
        log.verbose(f"  Skipping merging (no inclusion folder): {inclusion_dir}")
        return src_files, gen_images

    try:
        # Process filtered_src (src_files)
        for rel_path, data in filtered_src.items():
            new_rel_path = f"{rel_path[len(inclusion_dir):]}"
            src_files[new_rel_path] = data
            del src_files[rel_path] # Previous path is no longer needed
            log.debug(f"    Remapped file: {rel_path} -> {new_rel_path}")

        # Process filtered_img (gen_images)
        for dpi, png_files in filtered_img.items():
            for rel_path, data in png_files.items():
                new_rel_path = f"{rel_path[len(inclusion_dir):]}"
                gen_images[dpi][new_rel_path] = data
                del gen_images[dpi][rel_path] # Previous path is no longer needed
                log.debug(f"    Remapped gen. PNG: {rel_path} -> {new_rel_path} (DPI: {dpi})")

    except Exception as e:
        record_err(71, "inclusion_error", f"Error merging inclusions: {str(e)}")

    return src_files, gen_images
