# respackr/generate/sources.py

"""Contains methods for handling source files, primarily SourceLoader"""

import os
import re
from io import BytesIO
from pathlib import Path

from respackr import exceptions as rpe
from respackr import log


class SourceLoader(dict):
    """Loads sources upon calling load_sources and provides dict-like access."""

    def __init__(self, source_path: str, readonly: bool = False):
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


def extract_end_int(s):
    """Extracts an integer from the end of a string."""
    result = ""
    for char in reversed(s):
        if char.isdigit():
            result = char + result
        else:
            break
    return int(result) if result else None


sizes = [32, 64, 128]


class ProxyLoader(dict):
    """Acts as an intermediary between metadata and source files, storing any filedata generated
    by respackr.
    """

    def __init__(self, sources: SourceLoader, search_pattern: str):
        """Takes the loaded sources and regex searches all keys (paths) for resolution mappings

        A path can contain, but should *not end with* a special extension. Example:
            "textures/block.{search key}.png" or "texts/{search key}.credits" is valid, but:
            "textures/block.png.{search key}" is not.

        A path may also contain a directory named with a search pattern exactly. Example:
            "assets/textures/{search key}/..." is valid, but:
            "assets/textures/block{search key}/..." is not.

        Any given filepath can only contain at most *one* match. So:
            "assets/textures/{search key}/block/dirt_block.{search key}.png" would be invalid
            and will talley in `self.errors`. Invalid resolution numbers are also recorded.

        Found matches have the search key stripped out, effectively merging them into the parent,
        untagged filepath. This is handled by having each rel_path key being a nested dict
        containing scale ints extracted from the regex matches.

        Files without matches get stored at resolution 0, sharing the same rel_path value.

        Invalid resolution matches are kept track of in a `self.errors` dict.
        """

        # First part is the actual file name pattern, second part matches extensions or folders
        search_ext = search_pattern + r"(?:\.|\/)"
        self.errors = {
            "TooManyResolutionsWarning": {},
            "InvalidResolutionWarning": {},
            "InvalidResolutionDirectoryWarning": {},
        }
        proxy_dict = {}
        for rel_path in sources.keys():
            matches = list(re.finditer(search_ext, rel_path))

            # Check if the current path has more than one match (invalid)
            if len(matches) > 1:
                pretty_matches = ", ".join(f"({match.group(0)})" for match in matches)
                self.errors["TooManyResolutionsWarning"][rel_path] = {
                    "matches": pretty_matches,
                    "count": len(matches),
                    "exc_info": rpe.TooManyResolutionsWarning(
                        f"{len(matches)} resolution keys found at: {rel_path} (skipped file(s))"
                    ),
                }

                continue

            if matches:
                match = matches[0]

                size = int(match.group(1))
                if size not in sizes:
                    self.errors["InvalidResolutionWarning"][rel_path] = {
                        "size": size,
                        "exc_info": rpe.InvalidResolutionWarning(
                            f"{size} not in {sizes} at: {rel_path} (skipped file)"
                        ),
                    }
                    continue

                # Check if a matched directory is valid
                if "/" in match.group(0):
                    start_span = match.start(0)
                    # If the start character is at string begin then it's a valid (root dir) match
                    if start_span == 1:
                        pass
                    # Valid if immediately preceeded by a directory character
                    elif match.string[start_span - 1] == "/":
                        pass

                    else:  # Invalid if other checks fail.
                        # Skip if already logged
                        start_path = rel_path[: match.end(0)]
                        if start_path in self.errors:
                            self.errors["InvalidResolutionDirectoryWarning"][start_path][
                                "filecount"
                            ] += 1
                            continue

                        # Get the whole directory name
                        directory_match = ""
                        for i in range(match.start(0), -1, -1):
                            if rel_path[i] == "/":
                                directory_match = rel_path[i + 1 : match.end(0)]
                                break

                        self.errors["InvalidResolutionDirectoryWarning"][start_path] = {
                            "filecount": 1,
                            "exc_info": rpe.InvalidResolutionDirectoryWarning(
                                f"Matched directory '{directory_match}' is invalid at: {rel_path} (skipped directory)"
                            ),
                            "rel_path": rel_path,
                            "matched_dir": directory_match,
                        }
                        continue

                original_path = rel_path.replace(match.group(0), "")

                if original_path not in proxy_dict:
                    proxy_dict[original_path] = {}
                proxy_dict[original_path][size] = rel_path

            else:  # No resolution mappings found
                if rel_path not in proxy_dict:
                    proxy_dict[rel_path] = {0: rel_path}

                # This would trigger if a regex entry was found first
                if 0 not in proxy_dict[rel_path]:
                    proxy_dict[rel_path][0] = rel_path

        super().__init__(proxy_dict)

    def log_errors(self):
        """Logs any invalid filepaths (warnings) recorded during initialization."""
        for details in self.errors["TooManyResolutionsWarning"].values():
            log.warn(
                f"Paths should contain at most 1 resolution mapping. Found: {details['matches']}",
                exc_info=details["exc_info"],
            )
        for details in self.errors["InvalidResolutionWarning"].values():
            log.warn(
                f"The resolution '{details['size']}' is invalid.",
                exc_info=details["exc_info"],
            )
        for details in self.errors["InvalidResolutionDirectoryWarning"].values():
            log.warn(
                f"The directory '{details['matched_dir']}' ({details['filecount']} files) is invalid.",
                exc_info=details["exc_info"],
            )
