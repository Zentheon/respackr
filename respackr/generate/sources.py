# respackr/generate/sources.py

"""Contains methods for handling source files, primarily SourceLoader"""

import os
from io import BytesIO
from pathlib import Path

from respackr import log


class SourceLoader(dict):
    """Loads sources upon calling load_sources and provides dict-like access."""

    def __init__(self, source_path, readonly=False):
        """Initialize a SourceLoader instance with empty data.

        Args:
            source_path (str): Directory to load files from
            readonly (bool): Can be set to True at any time to block all modification of loaded
                files, including calling load_sources. Attempts to do so raise RuntimeError.
        """
        self.filecount = 0
        self.filetypes = {}
        self.source_path = Path(source_path)
        self.initial_load = False
        self.readonly = readonly

    def load_sources(self):
        """Loads source assets from the configured source directory.

        Also keeps track of extensions in a 'self.filetypes' dict.

        Raises:
            FileNotFoundError: When the provided directory doesn't exist.
            NotADirectoryError: When the provided directory is actually a file.
            RuntimeError: Raised by self.update() if in readonly mode.
        """
        if not self.source_path.exists():
            raise FileNotFoundError(f"Missing source directory: {self.source_path}")

        if not self.source_path.is_dir():
            raise NotADirectoryError(f"The provided path is not a directory: {self.source_path}")

        src_files = {}
        log.info("")
        log.info(f"Scanning source directory: {self.source_path}")

        # Walk through directory tree
        for root, _, files in os.walk(self.source_path):
            for filename in files:
                rel_path = (Path(root) / filename).relative_to(self.source_path)

                # Normalize paths
                rel_path = str(rel_path).replace("\\", "/")

                try:
                    file_path = Path(root) / filename
                    with open(file_path, "rb") as f:
                        src_files[str(rel_path)] = BytesIO(f.read())

                    log.debug(f"  Loaded: {rel_path}")

                except Exception as e:
                    log.error(f"Error loading {rel_path}", exc_info=e)
                    continue

        # Update total files count
        self.filecount = len(src_files)
        log.info("")
        log.info(f"Total files found: {self.filecount}")

        self.update(src_files)

        # Clear and update file types
        self.filetypes.clear()
        for rel_path, __ in self.items():
            ext = Path(rel_path).suffix.lower()
            if ext:
                if ext not in self.filetypes:
                    self.filetypes[ext] = 0
                self.filetypes[ext] += 1

        self.initial_load = True

    def __getitem__(self, key):
        """RuntimeError is raised if sources haven't been loaded first."""
        if not self.initial_load:
            raise RuntimeError("Sources have not been loaded yet. Call load_sources() first.")

        return super().__getitem__(key)

    def __setitem__(self, key, value):
        """RuntimeError is raised if SourceLoader is in readonly mode."""
        if self.readonly:
            raise RuntimeError("Sources are in read-only mode and cannot be modified.")
        super().__setitem__(key, value)

    def update(self, other=[], **kwargs):
        """RuntimeError is raised if SourceLoader is in readonly mode."""
        if self.readonly:
            raise RuntimeError("Sources are in read-only mode and cannot be modified.")
        super().update(other, **kwargs)
