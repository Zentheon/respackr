# makezip.py

# Revision of this module:
__version__ = "1.0.2"

import logging as log
import zipfile
import os

from modules.arguments import args
from modules.config import config
from modules.stats import talley
from modules.error import record_warn, record_err, record_crit

def create_zip_archive(zip_path, src_files, gen_images, cur_scale, cur_fmt):
    """
    Create the final ready-to-use resourcepack ZIPs.

    Args:
        zip_path (str): Full path to output file
        src_files (dict): Source files to pack
        gen_images (dict): Generated images to pack. Accepts `None`
        config.license_file (bool): Toggle whether to look for and include a license file
        config.allowed_paths (list): List of paths relative to `src_files` to allow
        cur_fmt (int): Format number for logging purposes
    Returns:
        (bool): True if a zip was created or --dry-run is flagged (unused)
    """
    if cur_scale is not None:
        cur_dpi = config.sorted_scales[cur_scale]

    if args.dry_run:
        log.verbose("")
        log.verbose(f"Dry run enabled, skipping creation of ZIP: {zip_path}")
        return True

    log.verbose("")
    log.verbose(f"Creating ZIP archive: {zip_path}")
    created_files = 0

    try:
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    except OSError as err:
        record_err(51, "directory_creation_error", f"Failed to create output directory: {str(err)}")
        return False

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Keep track of files already added to detect duplicates
            added_files_in_zip = set()

            # Add scale-specific pack.png, if present
            if f"scale_{cur_scale}.png" in src_files:
                zipf.writestr("pack.png", src_files[f"scale_{cur_scale}.png"])
                added_files_in_zip.add(f"scale_{cur_scale}.png")
                created_files += 1
                log.debug(f"  Added scale_{cur_scale}.png -> pack.png (DPI {cur_dpi})")

            # Add license, if provided
            if config.license_file and os.path.exists(config.license_file):
                try:
                    zipf.write(config.license_file)
                    added_files_in_zip.add(config.license_file)
                    created_files += 1
                    log.verbose(f"  Added license: {config.license_file}")
                except Exception as err:
                    record_err(53, "license_read_error",
                        f"Failed to read license file: {config.license_file}: {str(err)}")

            # Include files from src_files
            for rel_path, data in src_files.items():
                # Check if path matches any allowed_path prefix
                if any(rel_path.startswith(p) or rel_path == p for p in config.allowed_paths):
                    try:
                        zipf.writestr(rel_path, data)
                        added_files_in_zip.add(rel_path)
                        created_files += 1
                        log.debug(f"  Added file to ZIP: {rel_path}")
                    except Exception as err:
                        record_err(55, "zip_write_error",
                            f"Error writing file to ZIP: {str(err)}",
                            f"⤷ Path: {rel_path}")

            # Add generated PNGs for the current DPI
            if cur_scale is not None:
                if cur_dpi in gen_images:
                    for rel_path, data in gen_images[cur_dpi].items():
                        # Check if path matches any allowed_path prefix for generated PNGs
                        if any(rel_path.startswith(p) or rel_path == p for p in config.allowed_paths):
                            if rel_path in added_files_in_zip:
                                record_err(56, "duplicate_png",
                                    f"Attempted to add already-existing PNG to ZIP (DPI {cur_dpi})",
                                    f"⤷ Path: {rel_path}")
                                continue # Skip adding the duplicate
                            try:
                                zipf.writestr(rel_path, data)
                                added_files_in_zip.add(rel_path)
                                created_files += 1
                                log.debug(f"  Added gen. PNG to ZIP (DPI {cur_dpi}): {rel_path}")
                            except Exception as err:
                                record_err(57, "zip_write_error",
                                    f"Error writing generated PNG to ZIP: {str(err)}",
                                    f"⤷ Path: {rel_path}")

        if created_files > 0:
            talley['archives_created'] += 1

        log.verbose(f"  Total files added to ZIP: {created_files}")
        return True

    except Exception as err:
        record_err(52, "zip_creation_error", f"Error creating ZIP: {str(err)}")
        return False
