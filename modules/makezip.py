# makezip.py

# Revision of this module:
__version__ = "1.0.1"

import logging as log
import zipfile
import os

from modules.arguments import args
from modules.config import config
from modules.stats import talley
from modules.error import record_warn, record_err, record_crit

def create_zip_archive(zip_path, src_files, gen_images, scale, dpi, current_format):
    """
    Create the final ready-to-use resourcepack ZIPs.

    Args:
        zip_path (str): Full path to output file
        src_files (dict): Source files to pack
        gen_images (dict): Generated images to pack. Accepts `None`
        dpi (int): DPI value to add for gen_images. Accepts `None`
        config.license_file (bool): Toggle whether to look for and include a license file
        config.allowed_paths (list): List of paths relative to `src_files` to allow
        current_format (int): Format number for logging purposes
    Returns:
        (bool): True if a zip was created or --dry-run is flagged
    """
    if args.dry_run:
        log.verbose("")
        log.verbose(f"Dry run enabled, skipping creation of ZIP: {zip_path}")
        return True

    log.verbose("")
    log.verbose(f"Creating ZIP archive: {zip_path}")
    created_files = 0

    try:
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    except OSError as e:
        record_err(51, "directory_creation_error", f"Failed to create directory: {e}")
        return False

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Keep track of files already added to detect duplicates
            added_files_in_zip = set()

            # Add scale-specific pack.png, if present
            if f"scale_{scale}.png" in src_files:
                zipf.writestr("pack.png", src_files[f"scale_{scale}.png"])
                added_files_in_zip.add(f"scale_{scale}.png")
                created_files += 1
                log.debug(f"  Added scale_{scale}.png -> pack.png (DPI {dpi})")

            # Add license, if provided
            if config.license_file and os.path.exists(config.license_file):
                try:
                    zipf.write(config.license_file)
                    added_files_in_zip.add(config.license_file)
                    created_files += 1
                    log.verbose(f"  Added license: {config.license_file}")
                except Exception as e:
                    record_err(53, "license_read_error", f"Failed to read license file: {config.license_file}: {str(e)}")

            # Include files from src_files
            for rel_path, data in src_files.items():
                # Check if path matches any allowed_path prefix
                if any(rel_path.startswith(p) or rel_path == p for p in config.allowed_paths):
                    try:
                        zipf.writestr(rel_path, data)
                        added_files_in_zip.add(rel_path)
                        created_files += 1
                        log.debug(f"  Added file to ZIP: {rel_path}")
                    except Exception as e:
                        record_err(None, "zip_write_error", f"Error writing file {rel_path} to ZIP: {str(e)}")

            # Add generated PNGs for the current DPI
            if dpi is not None:
                if dpi in gen_images:
                    for rel_path, data in gen_images[dpi].items():
                        # Check if path matches any allowed_path prefix for generated PNGs
                        if any(rel_path.startswith(p) or rel_path == p for p in config.allowed_paths):
                            if rel_path in added_files_in_zip:
                                record_err(None, "duplicate_png",
                                    f"Attempted to add already-existing PNG to ZIP (DPI {dpi})",
                                    f"⤷ Path: {rel_path}")
                                continue # Skip adding the duplicate
                            try:
                                zipf.writestr(rel_path, data)
                                added_files_in_zip.add(rel_path)
                                created_files += 1
                                log.debug(f"  Added gen. PNG to ZIP (DPI {dpi}): {rel_path}")
                            except Exception as e:
                                record_err(None, "zip_write_error",
                                    f"Error writing generated PNG to ZIP: {str(e)}",
                                    f"⤷ Path: {rel_path}")

        if created_files > 0:
            talley['archives_created'] += 1

        log.verbose(f"  Total files added to ZIP: {created_files}")
        return True

    except Exception as e:
        record_err(None, "zip_creation_error", f"Error creating ZIP: {e}")
        return False
