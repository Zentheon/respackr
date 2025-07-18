# config.py

# Revision of this module:
__version__ = "1.0.1"

import json
from pathlib import Path
from types import SimpleNamespace
import logging as log

from modules.arguments import args
from modules.error import record_warn, record_err, record_crit

class ConfigLoader:
    """
    Loads a JSON config file and provides dot-notation access to nested keys.
    """

    def __init__(self):
        self._filepath = Path(args.config_file)
        log.debug(f"Config path: {self._filepath}")
        # Initialize variables
        self.config = None
        self._sorted_formats = {}
        self._sorted_scales = {}
        self.load_config()
        self.printouts()

    def load_config(self):
        # Load and validate config file
        try:
            if not self._filepath.exists():
                record_crit(4, "config_not_found", f"Config file not found at: {self._filepath}")

            with open(self._filepath, "r") as file:
                data = json.load(file)

            # Convert nested dictionaries into SimpleNamespace objects
            self.config = json.loads(json.dumps(data), object_hook=lambda d: SimpleNamespace(**d))
            log.trace("Loaded SimpleNamespace config:")
            log.trace(self.config)

        except json.JSONDecodeError as err:
            record_crit(6, "invalid_config", f"Invalid JSON in config file: {str(err)}")
        except Exception as err:
            record_crit(5, "config_load_fail", f"Failed to load config: {str(err)}")

    def __getattr__(self, key):
        # Allows dot notation access
        if not hasattr(self.config, key):
            # Throw an error if the key doesn't exist
            record_crit(7, "config_key_missing", f"Key '{key}' not found in config")
        log.trace(f"Accessed key config.{key}")
        return getattr(self.config, key)

    # Preprocessed items that can be accessed the same as dynamically loaded entries
    @property
    def sorted_formats(self):
        return self._sorted_formats
    @property
    def sorted_scales(self):
        return self._sorted_scales
    @property
    def color_map(self):
        return self._color_map

    def printouts(self):
        # Logging config attributes also serves as a handy shortcut to input
        # validation since __getattr__ already does exactly that
        log.info("")
        # Get pack name
        log.info(f"  Pack name: '{self.name}'")

        # Get pack description
        log.info(f"  Pack description: {self.description}")

        # Get source dir
        log.info(f"  Source directory: {self.source_dir}")

        # Get output dir
        log.info(f"  Output directory: {self.output_dir}")

        # Get license inclusion switch
        log.info(f"  Include license is set to: {self.license_file}")

        # Get allowed paths
        log.info(f"  Allowed path in output packs: {self.allowed_paths}")

        # Get max format addend
        log.info(f"  Most recent format compatibility buffer: {int(self.max_format)}")

        # Get format data
        formats_data = {int(k): v for k, v in self.formats.__dict__.items()}
        self._sorted_formats = dict(sorted(formats_data.items(), reverse=True))
        log.info("  Formats:")
        for k in self._sorted_formats.keys():
            log.info(f"    {k}: {self._sorted_formats[k]}")

        # Get svg processing toggle
        log.info(f"  SVG processing is set to: {self.process_svg_images}")

        # SVG processing-specific
        if self.process_svg_images == True:
            # Get scale mappings
            scales_data = {int(k): v for k, v in self.scales.__dict__.items()}
            self._sorted_scales = dict(sorted(scales_data.items(), reverse=True))
            log.info(f"  Scale mappings: {list(self._sorted_scales.keys())}")

            # Get theme dir
            log.info(f"  Theme directory: {self.theme_dir}")

            # Get default color mappings
            self._color_map = {k: v for k, v in self.default_colors.__dict__.items()}
            log.info("  Color mappings:")
            for k in self._color_map.keys():
                log.info(f"    {k}: {self._color_map[k]}")
        else:
            scales = None
            theme_dir = None
            default_colors = None

        log.info("")


# Singleton instance for easy import elsewhere
config = ConfigLoader()
