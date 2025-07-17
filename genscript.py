#!/usr/bin/env python
# genscript.py

# Basic script info
script_name = "respack-genscript"
script_ver = "v1.0.1"
script_desc = "Processes resourcepack sources and creates ready-to-use .zip files"

# Native imports
import os
import json
import zipfile
import logging as log
from pathlib import Path
from xml.etree import ElementTree as ET
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
    theme
)

def convert_svg_to_png(src_files, dpi_values_to_process):
    """
    Convert SVG content to PNG with resolution fetching and scaling.

    For whatever reason, the `dpi` parameter for CarioSVG does not work in Python,
    so we have to figure out the target width x height ourselves.

    Args:
        src_files (dict): Dictionary of source files, including SVG content.
        dpi_values_to_process (dict): Scales and their corresponding DPI values to generate images for.
    Returns:
        defaultdict: A dictionary of generated PNGs, keyed by DPI.
    """

    # Import CarioSVG now, since it's needed
    from cairosvg import svg2png

    log.trace("Called conver_svg_to_png")
    gen_images = defaultdict(dict)

    # Iterate over a copy of keys because we'll be modifying src_files
    for rel_path in list(src_files.keys()):
        if rel_path.lower().endswith('.svg'):
            log.debug(f"  Creating image(s) for SVG: {rel_path}")

            try:
                # Load content from `src_files` (already themed if theme was applied)
                svg_content = src_files[rel_path].decode('utf-8') if isinstance(src_files[rel_path], bytes) else src_files[rel_path]

                if svg_content is None:
                    record_err(42, "svg_load_error", f"Could not load SVG content for {rel_path}")
                    continue

                # Generate images for each DPI in the filtered list
                for scale, dpi in dpi_values_to_process.items():
                    log.trace(f"    Converting to PNG at target DPI {dpi}...")

                    # Parse SVG to get original dimensions
                    root = ET.fromstring(svg_content)
                    width_attr = root.get('width')
                    height_attr = root.get('height')

                    try:
                        width = float(width_attr[:-2]) if width_attr.endswith('pt') else float(width_attr)
                        height = float(height_attr[:-2]) if height_attr.endswith('pt') else float(height_attr)
                    except (ValueError, TypeError):
                        width, height = 1024, 1024
                        record_err(43, "svg_bad_dimensions", f"Using default 1024x2024 for {rel_path}")

                    scale_factor = dpi / 96.0
                    target_width = int(width * scale_factor)
                    target_height = int(height * scale_factor)

                    log.trace(f"    Original dimensions: {width}x{height}pt")
                    log.trace(f"    Target dimensions: {target_width}x{target_height}px")

                    png_data = svg2png(
                        bytestring=svg_content,
                        output_width=target_width,
                        output_height=target_height,
                        dpi=dpi,
                        scale=1.0,
                        unsafe=False
                    )

                    if not png_data:
                        record_err(43, "no_png_data", f"Empty PNG data returned for {rel_path}")

                    # Store in gen_images dictionary
                    gen_images[dpi][f"{rel_path[:-4]}.png"] = png_data
                    stats.svg_talley['png_files_generated'] += 1
                    log.trace(f"    Created PNG for Scale {scale} ({dpi} DPI): {rel_path[:-4]}.png")

                # Remove the SVG entry from src_files as it is no longer needed
                del src_files[rel_path]

            except Exception as e:
                record_err(41, "svg_processing_error", f"Error creating image for SVG: {str(e)}\n⤷ At: {rel_path}")

    log.verbose("")
    log.verbose(f"Total images created: {stats.svg_talley['png_files_generated']}")
    return gen_images

def apply_exclusions(current_format, src_files, gen_images):
    """
    Applies exclusion rules to both source files and generated images.
    Handles both file and directory paths.

    Args:
        current_format: The format key being processed
        config.source_dir: Source directory path
        src_files: Dictionary of original files
        gen_images: Dictionary of generated PNGs by DPI

    Returns:
        Tuple of (modified_src_files, modified_gen_images)
    """

    # Check for and load exlusion file from src_files
    if f"{current_format}.json" in src_files:
        log.verbose(f"  Found exclusion list: {current_format}.json")
        file_data = src_files[f"{current_format}.json"].decode('UTF8')
        exclusion_data = json.loads(file_data)
        # Normalize excluded paths
        excluded_paths = [p.replace('\\', '/').rstrip('/') for p in exclusion_data.get('exclusions')]
    else:
        log.verbose(f"  {current_format}.json not found, skipping exclusions")
        return src_files, gen_images

    try:
        for rel_path in list(src_files.keys()):
            normalized_rel_path = rel_path.replace('\\', '/').rstrip('/')

            # Check if path matches any exclusion file or directory
            for excluded_path in excluded_paths:
                if (normalized_rel_path == excluded_path or
                    normalized_rel_path.startswith(f"{excluded_path}/")):
                    if rel_path in src_files:
                        log.debug(f"    Excluding file: {rel_path}")
                        del src_files[rel_path]
                    else:
                        log.debug(f"    Skipped nonpresent entry in src_files: {rel_path}")

        # Process generated PNGs across all DPI variants
        for dpi, png_files in list(gen_images.items()):
            for rel_path in list(png_files.keys()):
                # Normalize excluded paths
                normalized_rel_path = rel_path.replace('\\', '/').rstrip('/')

                # Check PNG paths against exclusions
                for excluded_path in excluded_paths:
                    png_path = excluded_path[:-4] + '.png' if excluded_path.endswith('.svg') else excluded_path
                    png_path = png_path.rstrip('/')

                    if (normalized_rel_path == png_path or
                        normalized_rel_path.startswith(f"{png_path}/")):
                        if rel_path in png_files:
                            log.debug(f"    Excluding generated PNG: {rel_path} (DPI {dpi})")
                            del png_files[rel_path]
                        else:
                            log.debug(f"    Skipped nonpresent entry in gen_images: {rel_path}")

    except Exception as e:
        record_err(61, "exclusion_error", f"Error applying exclusions: {str(e)}")

    return src_files, gen_images

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

def generate_pack_mcmeta(current_format, scale, src_files):
    """
    Generates the pack.mcmeta file and adds it to src_files.
    Args:
        current_format (int): The current format key.
        config.sorted_formats (dict): Dictionary of all available config.sorted_formats.
        description (str): Base description for the pack.
        scale (int): The current scale being processed.
        src_files (dict): The dictionary of files to be included in the ZIP.
    """
    # Check for and remove previous pack.mcmeta
    pack_mcmeta_path = "pack.mcmeta"
    if pack_mcmeta_path in src_files:
        del src_files[pack_mcmeta_path]
        log.debug(f"  Removed existing {pack_mcmeta_path}")

    # Bump format to 1 if it's 0
    # "Format 0" packs are created due to a change in the
    # enchanting table UI in 1.7 without a format change.
    if current_format == 0:
      current_format = 1

    # Determine supported_formats range
    min_supported_format = current_format
    for key in config.sorted_formats.keys():
        if key < current_format:
            min_supported_format = key + 1
            break

    supported_formats_str = f"{min_supported_format}, {current_format}"

    # If scale is None (svg processing disabled), don't add a scale suffix
    def check_scale(scale):
        if scale is None:
            return ""
        else:
            return f" (Scale {scale})"

    # Create pack.mcmeta content
    pack_data = {
        "pack": {
            "pack_format": current_format,
            "supported_formats": [supported_formats_str],
            "description": f"{config.description}{check_scale(scale)}"
        }
    }
    # Convert to JSON string and then to bytes
    pack_mcmeta_content = json.dumps(pack_data, indent=4).encode('utf-8')
    # Add to src_files
    src_files[pack_mcmeta_path] = pack_mcmeta_content
    log.verbose(f"  Generated new {pack_mcmeta_path} with pack_format {current_format} and description '{config.description}{check_scale(scale)}")

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
                log.verbose(f"  Added scale_{scale}.png -> pack.png (DPI {dpi})")

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
                                record_err(None, "duplicate_png", f"Attempted to add already-existing PNG to ZIP (DPI {dpi})\n⤷ Path: {rel_path}")
                                continue # Skip adding the duplicate
                            try:
                                zipf.writestr(rel_path, data)
                                added_files_in_zip.add(rel_path)
                                created_files += 1
                                log.debug(f"  Added gen. PNG to ZIP (DPI {dpi}): {rel_path}")
                            except Exception as e:
                                record_err(None, "zip_write_error", f"Error writing generated PNG to ZIP: {str(e)}\n⤷ Path: {rel_path}")

        if created_files > 0:
            stats.talley['archives_created'] += 1

        log.verbose(f"  Total files added to ZIP: {created_files}")
        return True

    except Exception as e:
        record_err(None, "zip_creation_error", f"Error creating ZIP: {e}")
        return False

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
        gen_images = convert_svg_to_png(
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
        src_files, gen_images = apply_exclusions(
            current_format,
            src_files,
            gen_images
        )

        # Merge format-specific assets into the main assets directory, if they exist.
        # This call should happen AFTER exclusions are applied,
        # as we may want to move paths that would conflict in the place of others.
        src_files, gen_images = apply_inclusions(
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
                generate_pack_mcmeta(current_format, scale, src_files)

                zip_name = f"{config.name}-{args.packver}-{config.sorted_formats[current_format]}-scale-{scale}.zip"
                zip_path = os.path.join(config.output_dir, str(current_format), zip_name)
                log.debug(f"  ZIP path to write: {zip_path}")
                create_zip_archive(
                    zip_path,
                    src_files,
                    gen_images,
                    scale,
                    dpi,
                    current_format
                )
        else: # Regular pack creation
            generate_pack_mcmeta(current_format, None, src_files)

            zip_name = f"{config.name}-{args.packver}-{config.sorted_formats[current_format]}.zip"
            zip_path = os.path.join(config.output_dir, zip_name)
            log.debug(f"  ZIP path to write: {zip_path}")
            create_zip_archive(
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
