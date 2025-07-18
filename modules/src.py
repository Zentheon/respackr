# src.py

# Revision of this module:
__version__ = "1.0.1"

import os
import logging as log

from modules.arguments import args
from modules.config import config
from modules.stats import talley, file_extensions
from modules.error import record_warn, record_err, record_crit

def scan_src_files():
    """
    Scans and loads all files from the configured source directory into a dictionary.
    Counts different file types in the proc_stats talley.

    Returns:
        dict: Dictionary mapping relative paths to file contents
    """
    if not os.path.exists(config.source_dir):
        record_crit(11, "missing_source_dir", f"Missing source directory: {config.source_dir}")

    src_files = {}
    log.info("")
    log.info(f"Scanning source directory: {config.source_dir}")

    # Walk through directory tree
    for root, dirs, files in os.walk(config.source_dir):
        for filename in files:
            rel_path = os.path.relpath(os.path.join(root, filename), config.source_dir)

            # Normalize paths
            rel_path = rel_path.replace('\\', '/')

            try:
                with open(os.path.join(root, filename), 'rb') as f:
                    file_content = f.read()

                    # Track file extensions in talley
                    ext = os.path.splitext(filename)[1].lower()
                    if ext:
                        file_extensions[ext] += 1

                    src_files[rel_path] = file_content
                    log.debug(f"  Loaded: {rel_path}")

            except Exception as err:
                record_err(12, "file_load_error", f"Error loading {rel_path}: {str(err)}")
                continue

    # Update total files count
    talley['source_files_loaded'] = len(src_files)
    log.info("")
    log.info(f"Total files found: {len(src_files)}")

    return src_files
