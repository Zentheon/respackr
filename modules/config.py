# config.py

# Revision of this module:
__version__ = "1.1.0"

import json
import os
from pathlib import Path
from types import SimpleNamespace
import logging as log

from modules.arguments import args
from modules.error import record_warn, record_err, record_crit

class ConfigLoader:
    """
    Loads a JSON config file and provides dot-notation access to nested keys.

    Supports optional entries, graceful handling of malformed configs and (basic) validation.
    Also prints out a nice list of values.
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
        self.validate_extra()

    def load_config(self):
        # Load and validate config file
        try:
            if not self._filepath.exists():
                record_crit(4, "config_not_found", f"Config file not found at: {self._filepath}")

            with open(self._filepath, "r") as file:
                data = json.load(file)

            # Convert nested dictionaries into SimpleNamespace objects
            config_dict = {}
            for key, value in data.items():
                if isinstance(value, dict):
                    config_dict[key] = json.loads(json.dumps(value), object_hook=lambda d: SimpleNamespace(**d))
                else:
                    config_dict[key] = value

            self.config = SimpleNamespace(**config_dict)
            log.trace("Loaded SimpleNamespace config:")
            log.trace(self.config)

            # Optional entries that should be None if not present
            for attr_name in [
                'license_file',
                'scales',
                'process_svg_images',
                'default_colors',
                'theme_dir'
            ]:
                setattr(self.config, attr_name, config_dict.get(attr_name, None))
                log.trace(f"Optional attribute {attr_name} set to: {getattr(self.config, attr_name)}")

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

    def validate_extra(self):
        """Extra validation of certain properties where applicable"""
        # Validate format argument
        if args.format:
            if not args.format in self.sorted_formats:
              record_crit(21, "format_not_found", f"Specified format: {args.format} not present in {self.sorted_formats} 'formats'")

        # Validate license, if provided
        if self.license_file:
            if not os.path.exists(self.license_file):
                record_crit(52, "license_not_found", f"License file does not exist: {self.license_file}")

        # Filter config.sorted_scales and check if args.scale is valid
        if args.scale is not None and self.process_svg_images:
            if args.scale in self.sorted_scales:
                self._sorted_scales = {args.scale: self.sorted_scales[args.scale]}
                log.info("")
                log.info(f"Generating only for scale {args.scale} ({self.sorted_scales[args.scale]} DPI)")
            else:
                record_crit(22, "scale_not_found", f"Specified scale '{args.scale}' not found in buildcfg.json")

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

    def validate_type(self, key, expected_type):
        """Checks for the expected type in the input value"""
        value = getattr(self, key, None)
        if isinstance(value, expected_type):
            return value
        else:
            exp_type_name = expected_type.__name__.title()
            got_type_name = type(value).__name__.title()
            record_crit(8, "invalid_config_datatype",
                f"Expected {key} to be {exp_type_name}, but got {got_type_name}: {value}")

    def printouts(self):
        """
        Prints a nice list of configuration values.

        Also validates datatypes with validate_type and checks for
        missing entries thanks to __getattr__'s error handling.
        """
        log.info("")
        # Get pack name
        log.info(f"  Pack name: '{self.validate_type('name', str)}'")

        # Get source dir
        log.info(f"  Source directory: {self.validate_type('source_dir', str)}")

        # Get output dir
        log.info(f"  Output directory: {self.validate_type('output_dir', str)}")

        # Get license inclusion switch
        log.info(f"  Include license is set to: {self.validate_type('license_file', str)}")

        # Get allowed paths
        log.info(f"  Allowed path in output packs: {self.validate_type('allowed_paths', list)}")

        # Get max format addend
        log.info(f"  Most recent format compatibility buffer: {self.validate_type('max_format', int)}")

        # Get format data
        self.validate_type('formats', SimpleNamespace)
        formats_data = {int(k): v for k, v in self.formats.__dict__.items()}
        self._sorted_formats = dict(sorted(formats_data.items(), reverse=True))
        log.info("  Formats:")
        for k in self._sorted_formats.keys():
            log.info(f"    {k}: {self._sorted_formats[k]}")

        # Get svg processing toggle
        log.info(f"  SVG processing is set to: {self.validate_type('process_svg_images', bool)}")

        # SVG processing-specific
        if self.process_svg_images == True:
            # Get scale mappings
            self.validate_type('scales', SimpleNamespace)
            scales_data = {int(k): v for k, v in self.scales.__dict__.items()}
            self._sorted_scales = dict(sorted(scales_data.items(), reverse=True))
            log.info(f"  Scale mappings: {list(self._sorted_scales.keys())}")

            # Get theme dir
            log.info(f"  Theme directory: {self.validate_type('theme_dir', str)}")

            # Get default color mappings
            self.validate_type('default_colors', SimpleNamespace)
            self._color_map = {k: v for k, v in self.default_colors.__dict__.items()}
            log.info("  Color mappings:")
            for k in self._color_map.keys():
                log.info(f"    {k}: {self._color_map[k]}")

        log.info("") # Spacer


# Singleton instance for easy import elsewhere
config = ConfigLoader()
