#!/usr/bin/env python
# genscript.py

# Basic script info
script_name = "respack-genscript"
script_ver = "v2.0.0"
script_desc = "Processes resourcepack sources and creates ready-to-use .zip files"

# Native imports
import os
import json
import logging as log
from collections import defaultdict

# Arguments should be set up first
from modules.arguments import create_args
create_args(script_name, script_desc, script_ver)
from modules.arguments import args

# Logging is auto-initialized on import
import modules.log

# Load the rest
from modules.error import record_warn, record_err, record_crit
from modules.config import config
from modules import (
    stats,
    src,
    theme,
    svg2png,
    exclusion,
    inclusion,
    mcmeta,
    makezip
)

def main():
    log.info(f"{script_name} {script_ver}")
    log.info("Starting pack generation pipeline...")

    # Validate config.sorted_formats
    if args.format:
        if not args.format in config.sorted_formats:
          record_err(21, "format_not_found", f"Specified format: {args.format} not present in {config_file} 'formats'")

    # Validate license, if provided
    if config.license_file:
        if not os.path.exists(config.license_file):
            record_err(52, "license_not_found", f"License file does not exist: {config.license_file}")

    # Filter config.sorted_scales and check if args.scale is valid
    if args.scale is not None and config.process_svg_images:
        if args.scale in config.sorted_scales:
            dpi_values_to_process = {args.scale: config.sorted_scales[args.scale]}
            log.info("")
            log.info(f"Generating only for scale {args.scale} ({config.sorted_scales[args.scale]} DPI)")
        else:
            record_err(22, "scale_not_found", f"Specified scale '{args.scale}' not found in buildcfg.json")

    else:
        dpi_values_to_process = config.sorted_scales

    # src_files will be populated with the original `./src` tree.
    src_files = src.scan_src_files()
    # gen_images will be populated later by PNGs generated from SVGs, with the root keys as DPI.
    gen_images = defaultdict(dict)

    # SVG editing and PNG generation
    if config.process_svg_images == True:
        gen_images = defaultdict(dict)
        log.info("")
        log.info("Processing SVG files...")
        svg_files_processed = 0

        # Apply theme to all SVG files in src_files
        src_files = theme.apply_theme(
            src_files,
            args.theme,
        )

        # Iterate over a copy of keys because we'll be modifying src_files
        gen_images = svg2png.convert_svg_to_png(
            src_files,
            dpi_values_to_process
        )

    # Process config.sorted_formats and create ZIPs
    log.info("")
    log.info("Processing config.sorted_formats and creating ZIP archives...")

    for current_format in config.sorted_formats.keys():
        # Break loop if current `current_format` is lower than `args.format` (Pack would have been created by the previous loop)
        if args.format is not None and current_format < args.format:
            log.verbose("")
            log.verbose(f"Ending processing as current format {current_format} is lower than specified --format-key {args.format}")
            break

        stats.talley['formats_processed'] += 1

        log.verbose("")
        log.verbose(f"Processing format: {current_format}")

        # Check for and process a format-specific .json file in `./src`
        # with an "exclusions" list.
        src_files, gen_images = exclusion.apply_exclusions(
            current_format,
            src_files,
            gen_images
        )

        # Merge format-specific assets into the main assets directory, if they exist.
        # This call should happen AFTER exclusions are applied,
        # as we may want to move paths that would conflict in the place of others.
        src_files, gen_images = inclusion.apply_inclusions(
            current_format,
            src_files,
            gen_images
        )
        # Skip zip creation if format flag is given and not matching current pass.
        if args.format is not None and current_format != args.format:
            log.verbose(f"  Skipping .zip creation of format: {current_format} (not the specified --format-key)")
            continue

        # Only create per-scale packs if config.process_svg_images is True
        if config.process_svg_images == True:
            for scale, dpi in dpi_values_to_process.items():
                mcmeta.generate_pack_mcmeta(current_format, scale, src_files)

                zip_name = f"{config.name}-{args.packver}-{config.sorted_formats[current_format]}-scale-{scale}.zip"
                zip_path = os.path.join(config.output_dir, str(current_format), zip_name)
                log.debug(f"  ZIP path to write: {zip_path}")
                makezip.create_zip_archive(
                    zip_path,
                    src_files,
                    gen_images,
                    scale,
                    dpi,
                    current_format
                )
        else: # Regular pack creation
            mcmeta.generate_pack_mcmeta(current_format, None, src_files)

            zip_name = f"{config.name}-{args.packver}-{config.sorted_formats[current_format]}.zip"
            zip_path = os.path.join(config.output_dir, zip_name)
            log.debug(f"  ZIP path to write: {zip_path}")
            makezip.create_zip_archive(
                zip_path,
                src_files,
                None,
                None,
                None,
                current_format
            )

    log.info("")
    log.info("Done!")
    if not args.dry_run:
        log.info(f"Output available in {config.output_dir}")
    else:
        log.info("No files created (--dry-run)")

    # Print final summary
    if not args.quiet:
        stats.print_summary()

if __name__ == "__main__":
    main()
