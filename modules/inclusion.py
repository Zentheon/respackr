# inclusion.py

# Revision of this module:
__version__ = "1.0.1"

import logging as log
import json

from modules.arguments import args
from modules.config import config
from modules.error import record_warn, record_err, record_crit

def apply_inclusions(cur_fmt, src_files, gen_images):
    """
    Merges assets from format-specific directories into root source directory.

    Args:
        cur_fmt (int): The current format key being processed.
        src_files (dict): Dictionary of original files.
        gen_images (defaultdict): Dictionary of generated PNGs by DPI.

    Returns:
        Tuple of (modified_src_files, modified_gen_images)
    """

    # Function to match gen_images inclusions
    def gen_images_filter(gen_images, inc_dir):
        filtered_img = {}
        for dpi, value in gen_images.items():
            if isinstance(value, dict):
                sub_matches = {k: v for k, v in value.items() if k.startswith(str(inc_dir))}
                if sub_matches:  # Only add if there are matches
                    log.trace(f"  Matched gen_png inclusions")
                    filtered_img[dpi] = sub_matches

        return filtered_img

    # Initial dictionaries
    inc_dir = f"{cur_fmt}/"
    filtered_src = {k: v for k, v in src_files.items() if k.startswith(inc_dir)}
    filtered_img = gen_images_filter(gen_images, inc_dir)

    # Check if any entries were found
    if filtered_src or filtered_img:
        log.verbose(f"  Merging format inclusion folder: {inc_dir}")
    else:
        log.verbose(f"  Skipping merging (no inclusion folder): {inc_dir}")
        return src_files, gen_images

    try:
        # Process filtered_src (src_files)
        for rel_path, data in filtered_src.items():
            try:
                new_rel_path = f"{rel_path[len(inc_dir):]}"
                src_files[new_rel_path] = data
                del src_files[rel_path] # Previous path is no longer needed
                log.debug(f"    Remapped file: {rel_path} -> {new_rel_path}")
            except Exception as err:
                record_err:(72, "file_inclusion_error",
                    f"Error merging file: {str(err)}",
                    f"⤷ Path: {rel_path}")

        # Process filtered_img (gen_images)
        for dpi, png_files in filtered_img.items():
            for rel_path, data in png_files.items():
                try:
                    new_rel_path = f"{rel_path[len(inc_dir):]}"
                    gen_images[dpi][new_rel_path] = data
                    del gen_images[dpi][rel_path] # Previous path is no longer needed
                    log.debug(f"    Remapped gen. PNG: {rel_path} -> {new_rel_path} (DPI: {dpi})")
                except Exception as err:
                    record_err:(73, "gen_png_inclusion_error",
                        f"Error merging gen. PNG: {str(err)}",
                        f"⤷ Path: {rel_path}")

    except Exception as err:
        record_crit(71, "inclusion_error", f"Error merging inclusions: {str(err)}")

    return src_files, gen_images
