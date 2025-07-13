# genscript.py
import os
import json
import zipfile
import argparse
from pathlib import Path
from xml.etree import ElementTree as ET
from collections import defaultdict

# Basic script info
script_name = "respack-genscript"
script_ver = "v1.0.0"
config_file = './buildcfg.json'

# Configure argument parsing
def parse_args():
    parser = argparse.ArgumentParser(
        prog=f"{script_name}",
        description="Processes resourcepack sources and creates ready-to-use .zip files"
        )

    parser.add_argument('--version', action='version', version=f'%(prog)s {script_ver}')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print out live status info and error messages')
    parser.add_argument('-vv', '--very-verbose', action='store_true', help='Print out each path as it is accessed')
    parser.add_argument('-q', '--quiet', action='store_true', help='Run without any feedback')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Skip writing .zip archives to disk')
    parser.add_argument('--theme', type=str, help='Specify a theme to apply color mappings from (e.g., "--theme=nord")')
    parser.add_argument('--scale', type=int, help='Generate only for a specific scale (e.g., "--scale=3" for 72DPI)')
    parser.add_argument('--format', type=int, help='Generate only for a specific format key (e.g., "--format-key=18")')
    parser.add_argument('--packver', default='dev', type=str, help='Pack version string to use. Defaults to "dev"')
    return parser.parse_args()

args = parse_args()

# Initialize statistics tracking variables
proc_stats = {
    'talley': {
        'formats_processed': 0,
        'archives_created': 0,
        'source_files_loaded': 0,
    },
    'svg_talley': {
        'theme_color_stats': {},
        'svg_files_edited': 0,
        'png_files_generated': 0,
    },
    'file_extensions': {},
    'errors': defaultdict(int)
}

def record_error(exit_code, error_type, message):
    """
    Error logging. If exit_code is None, the error is considered nonfatal.
    Code contexts in the scope of this script:
        4-10: Problems with configuration file
        11-20: Source scan problems
        21-30: Incorrect flag values
        31-40: SVG theming-specific
        51-60: ZIP creation-specific
    """
    proc_stats['errors'][error_type] += 1
    # Quit execution if exit_code is provided
    if exit_code is not None:
        quiet_print(f"\nError ({error_type}): {message}. Exiting.")
        exit(exit_code)

    verbose_print(f"Error ({error_type}): {message}")

def verbose_print(*messages):
    if args.verbose and not args.quiet:
        print(*messages)
    elif args.very_verbose and not args.quiet:
        print(*messages)

def very_verbose_print(*messages):
    if args.very_verbose and not args.quiet:
        print(*messages)

def quiet_print(*messages):
    if not args.quiet:
        print(*messages)

def print_summary():
    """
    Various tallies are kept track of during the script,
    which can give insights into problems with the pack or script.
    """

    if args.quiet:
        return

    talley = proc_stats['talley']
    svg_talley = proc_stats['svg_talley']

    print("\n======= SUMMARY =======")

    print("\nTalley:")
    print(f"- Total files loaded: {talley['source_files_loaded']}")
    print(f"- Formats processed: {talley['formats_processed']}")
    print(f"- Resourcepack ZIPs written: {talley['archives_created']}")

    print("\nLoaded Filetypes:")
    for filetype, amount in sorted(proc_stats['file_extensions'].items(), key=lambda item: item[1], reverse=True):
        print(f"- {filetype.lstrip('.')} ({amount})")

    # SVG editing-specific
    if svg_talley['png_files_generated']:
        print("\nSVG Talley:")
        print(f"- SVG files themed: {svg_talley['svg_files_edited']}")
        print(f"- PNG files generated: {svg_talley['png_files_generated']}")

    if svg_talley['theme_color_stats']:
        print("\nColors applied to SVG objects:")
        for color, amount in sorted(svg_talley['theme_color_stats'].items(), key=lambda item: item[1], reverse=True):
            print(f"- {color.lstrip('.')}: {amount}")

    print("\nErrors:")
    if proc_stats['errors']:
        for error, count in sorted(proc_stats['errors'].items()):
            print(f"- {error}: {count}")
    else:
        print("- No errors recorded")
    print("========================")

def load_config(config_file):
    # TODO: Possibly make config loading dynamic

    # Make sure config actually exists
    if not os.path.exists(config_file):
        record_error(4, "missing_config_file", f"Missing configuration file: {config_file}")

    verbose_print(f"\nLoading config file: {config_file}")
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            # Get pack name
            pack_name = config.get('name')
            quiet_print(f"\n  Pack name: '{pack_name}'")

            # Get pack description
            pack_description = config.get('description')
            quiet_print(f"  Pack description: {pack_description}")

            # Get source dir
            source_dir = config.get('source_dir')
            quiet_print(f"  Source directory: {source_dir}")

            # Get output dir
            output_dir = config.get('output_dir')
            quiet_print(f"  Output directory: {output_dir}")

            # Get license inclusion switch
            license_file = config.get('license_file')
            quiet_print(f"  Include license is set to: {license_file}")

            # Get allowed paths
            allowed_paths = config.get('allowed_paths', [])
            quiet_print(f"  Output directory: {allowed_paths}")

            # Get format data
            formats_data = {int(k): v for k, v in config['formats'].items()}
            sorted_formats = dict(sorted(formats_data.items(), reverse=True))
            quiet_print(f"  Formats: {list(sorted_formats.keys())}")

            # Get svg processing toggle
            svg_process_toggle = config.get('process_svg_images')
            quiet_print(f"  SVG processing is set to: {svg_process_toggle}")

            # SVG processing-specific
            if svg_process_toggle == True:
                # Get scale mappings
                scales = {int(k): v for k, v in config.get('scales', {}).items()}
                quiet_print(f"  Scale mappings: {list(scales.keys())}")

                # Get theme dir
                theme_dir = config.get('theme_dir')
                quiet_print(f"  Output directory: {theme_dir}")

                # Get default color mappings
                default_colors = config.get('default_colors', {})
                quiet_print(f"  Color mappings: {list(default_colors.keys())}")
            else:
                scales = None
                theme_dir = None
                default_colors = None

            return(
                pack_name,
                pack_description,
                source_dir,
                output_dir,
                license_file,
                allowed_paths,
                sorted_formats,
                svg_process_toggle,
                scales,
                theme_dir,
                default_colors
                )

    except Exception as e:
        record_error(5, "config_load_error", f"\nError loading config: {str(e)}")

def scan_src_files(source_dir):
    """
    Scans and loads all files from the source directory into a dictionary.
    Counts different file types in the proc_stats talley.

    Args:
        source_dir (str): Path to the source directory to scan

    Returns:
        dict: Dictionary mapping relative paths to file contents
    """
    if not os.path.exists(source_dir):
        record_error(11, "missing_source_dir", f"Missing source directory: {source_dir}")

    src_files = {}
    quiet_print(f"\nScanning source directory: {source_dir}")

    # Walk through directory tree
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            rel_path = os.path.relpath(os.path.join(root, filename), source_dir)

            # Convert Windows paths to Unix-style if needed
            rel_path = rel_path.replace('\\', '/')

            try:
                with open(os.path.join(root, filename), 'rb') as f:
                    file_content = f.read()

                    # Track file extensions in talley
                    ext = os.path.splitext(filename)[1].lower()
                    if ext:
                        if ext not in proc_stats['file_extensions']:
                            proc_stats['file_extensions'][ext] = 0
                        proc_stats['file_extensions'][ext] += 1


                    src_files[rel_path] = file_content
                    very_verbose_print(f"  Loaded: {rel_path}")

            except Exception as e:
                record_error(None, "file_load_error", f"Error loading {rel_path}: {str(e)}")
                continue

    # Update total files count
    proc_stats['talley']['source_files_loaded'] = len(src_files)
    quiet_print(f"\nTotal files found: {len(src_files)}")

    return src_files


def apply_theme(src_files, theme_dir, theme_name, default_colors):
    """
    Replaces colors in SVG content based on a theme's color map JSON file and default colors as search keys.
    Iterates through src_files and modifies SVG content in place.
    Args:
        src_files (dict): The dictionary of source files.
        theme_dir (str): Directory where theme JSON files are located.
        theme_name (str): The name of the theme to load (e.g., "nord").
            If None, no theme is applied.
        default_colors (dict, optional): A dictionary of default color keys to their hex values
            (e.g., {'primary': '#RRGGBB'}).
    Returns:
        dict: The modified src_files dictionary with themed SVG content.
    """
    if not theme_name:
        verbose_print(f"  Skipping theme edits (no theme specified)")
        return src_files

    if not os.path.isdir(theme_dir):
        record_error(31, "theme_dir_not_found", f"Theme directory: '{theme_dir}' is not valid.")
        return src_files

    theme_file = os.path.join(theme_dir, f"{theme_name}.json")
    if not os.path.exists(theme_file):
        record_error(32, "theme_file_not_found", f"Theme file not found: {theme_file}")
        return src_files

    try:
        with open(theme_file, 'r') as f:
            theme_data = json.load(f)
            theme_color_map = theme_data.get('colors', {})

        verbose_print(f"  Editing with theme '{theme_name}':")
        for rel_path in list(src_files.keys()):
            very_verbose_print("check")
            if rel_path.lower().endswith('.svg'):
                very_verbose_print(f"    Applying theme to SVG: {rel_path}")
                svg_content = src_files[rel_path].decode('utf-8') if isinstance(src_files[rel_path], bytes) else src_files[rel_path]
                if svg_content is None:
                    record_error(None, "svg_load_error", f"Could not load SVG content for {rel_path}")
                    continue

                final_color_map = {}
                if default_colors:
                    for default_color_key, default_hex_color in default_colors.items():
                        if default_color_key in theme_color_map and default_hex_color in svg_content:
                            color_count = svg_content.count(default_hex_color)

                            # Stat logging
                            proc_stats['svg_talley']['svg_files_edited'] += 1
                            color_stat = f"{default_color_key} ({default_hex_color} -> {theme_color_map[default_color_key]})"
                            if color_stat not in proc_stats['svg_talley']['theme_color_stats']:
                                proc_stats['svg_talley']['theme_color_stats'][color_stat] = 0
                            proc_stats['svg_talley']['theme_color_stats'][color_stat] += color_count

                            final_color_map[default_hex_color.lower()] = theme_color_map[default_color_key].lower()
                            very_verbose_print(f"      Mapping {color_count} instances of color '{default_color_key}': '{default_hex_color}' -> '{theme_color_map[default_color_key]}'")
                        else:
                            final_color_map[default_hex_color.lower()] = default_hex_color.lower()
                            very_verbose_print(f"      No theme color for '{default_color_key}', keeping default '{default_hex_color}'")

                # Apply all color replacements
                themed_svg = svg_content
                for original_color, new_color in final_color_map.items():
                    themed_svg = themed_svg.replace(original_color, new_color)

                src_files[rel_path] = themed_svg.encode('utf-8') # Update the src_files with themed SVG content

    except Exception as e:
        record_error(None, "theme_processing_error", f"Error processing theme '{theme_name}': {str(e)}")

    return src_files

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

    gen_images = defaultdict(dict)

    # Iterate over a copy of keys because we'll be modifying src_files
    for rel_path in list(src_files.keys()):
        if rel_path.lower().endswith('.svg'):
            very_verbose_print(f"\nCreating PNG for SVG: {rel_path}")

            try:
                # Load content from `src_files` (already themed if theme was applied)
                svg_content = src_files[rel_path].decode('utf-8') if isinstance(src_files[rel_path], bytes) else src_files[rel_path]

                if svg_content is None:
                    record_error(None, "svg_load_error", f"Could not load SVG content for {rel_path}")
                    continue

                # Generate images for each DPI in the filtered list
                for scale, dpi in dpi_values_to_process.items():
                    very_verbose_print(f"  Converting to PNG at target DPI {dpi}...")

                    # Parse SVG to get original dimensions
                    root = ET.fromstring(svg_content)
                    width_attr = root.get('width')
                    height_attr = root.get('height')

                    try:
                        width = float(width_attr[:-2]) if width_attr.endswith('pt') else float(width_attr)
                        height = float(height_attr[:-2]) if height_attr.endswith('pt') else float(height_attr)
                    except (ValueError, TypeError):
                        width, height = 1024, 1024
                        record_error(None, "svg_dimensions_warning", f"Using default 1024x2024 for {rel_path}")

                    scale_factor = dpi / 96.0
                    target_width = int(width * scale_factor)
                    target_height = int(height * scale_factor)

                    very_verbose_print(f"  Original dimensions: {width}x{height}pt")
                    very_verbose_print(f"  Target dimensions: {target_width}x{target_height}px")

                    png_data = svg2png(
                        bytestring=svg_content,
                        output_width=target_width,
                        output_height=target_height,
                        dpi=dpi,
                        scale=1.0,
                        unsafe=False
                    )

                    if not png_data:
                        record_error(None, "no_png_data", f"Empty PNG data returned for {rel_path}")

                    # Store in gen_images dictionary
                    gen_images[dpi][f"{rel_path[:-4]}.png"] = png_data
                    proc_stats['svg_talley']['png_files_generated'] += 1
                    very_verbose_print(f"  Created PNG for Scale {scale} ({dpi} DPI): {rel_path[:-4]}.png")

                # Remove the SVG entry from src_files as it is no longer needed
                del src_files[rel_path]

            except Exception as e:
                record_error(None, "svg_processing_error", f"Error creating image for SVG: {str(e)}\n⤷ At: {rel_path}")

    verbose_print(f"\nTotal images created: {proc_stats['svg_talley']['png_files_generated']}")
    return gen_images

def apply_exclusions(current_format, source_dir, src_files, gen_images):
    """
    Applies exclusion rules to both source files and generated images.
    Handles both file and directory paths.

    Args:
        current_format: The format key being processed
        source_dir: Source directory path
        src_files: Dictionary of original files
        gen_images: Dictionary of generated PNGs by DPI

    Returns:
        Tuple of (modified_src_files, modified_gen_images)
    """

    # Check for and load exlusion file from src_files
    if f"{current_format}.json" in src_files:
        verbose_print(f"  Found {current_format}.json")
        file_data = src_files[f"{current_format}.json"].decode('UTF8')
        exclusion_data = json.loads(file_data)
        # Normalize excluded paths
        excluded_paths = [p.replace('\\', '/').rstrip('/') for p in exclusion_data.get('exclusions')]
    else:
        verbose_print(f"  {current_format}.json not found, skipping exclusions")
        return src_files, gen_images

    try:
        for rel_path in list(src_files.keys()):
            normalized_rel_path = rel_path.replace('\\', '/').rstrip('/')

            # Check if path matches any exclusion file or directory
            for excluded_path in excluded_paths:
                if (normalized_rel_path == excluded_path or
                    normalized_rel_path.startswith(f"{excluded_path}/")):
                    if rel_path in src_files:
                        very_verbose_print(f"    Excluding file: {rel_path}")
                        del src_files[rel_path]
                    else:
                        very_verbose_print(f"    Skipped nonpresent entry in src_files: {rel_path}")

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
                            very_verbose_print(f"    Excluding generated PNG: {rel_path} (DPI {dpi})")
                            del png_files[rel_path]
                        else:
                            very_verbose_print(f"    Skipped nonpresent entry in gen_images: {rel_path}")

    except Exception as e:
        record_error(None, "exclusion_error", f"Error applying exclusions: {str(e)}")

    very_verbose_print()
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
    verbose_print(f"  Merging assets for format: {current_format}")

    # Process src_files
    try:
        new_src_files = {}
        for rel_path, data in src_files.items():
            prefix = f"{current_format}/"
            if rel_path.startswith(prefix):
                new_rel_path = f"{rel_path[len(prefix):]}"
                new_src_files[new_rel_path] = data
                very_verbose_print(f"    Remapped file: {rel_path} -> {new_rel_path}")
            else:
                new_src_files[rel_path] = data

        # Process gen_images
        new_gen_images = defaultdict(dict)
        for dpi, png_files in gen_images.items():
            for rel_path, data in png_files.items():
                prefix = f"{current_format}/"
                if rel_path.startswith(prefix):
                    new_rel_path = f"{rel_path[len(prefix):]}"
                    new_gen_images[dpi][new_rel_path] = data
                    very_verbose_print(f"    Remapped gen. PNG: {rel_path} -> {new_rel_path} (DPI: {dpi})")
                else:
                    new_gen_images[dpi][rel_path] = data

    except Exception as e:
        record_error(None, "inclusion_error", f"Error merging inclusions: {str(e)}")

    very_verbose_print()
    return new_src_files, new_gen_images

def generate_pack_mcmeta(current_format, formats, pack_description, scale, src_files):
    """
    Generates the pack.mcmeta file and adds it to src_files.
    Args:
        current_format (int): The current format key.
        formats (dict): Dictionary of all available formats.
        description (str): Base description for the pack.
        scale (int): The current scale being processed.
        src_files (dict): The dictionary of files to be included in the ZIP.
    """
    # Check for and remove previous pack.mcmeta
    pack_mcmeta_path = "pack.mcmeta"
    if pack_mcmeta_path in src_files:
        del src_files[pack_mcmeta_path]
        very_verbose_print(f"  Removed existing {pack_mcmeta_path}")

    # Bump format to 1 if it's 0
    # "Format 0" packs are created due to a change in the
    # enchanting table UI in 1.7 without a format change.
    if current_format == 0:
      current_format = 1

    # Determine supported_formats range
    min_supported_format = current_format
    for key in formats.keys():
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
            "description": f"{pack_description}{check_scale(scale)}"
        }
    }
    # Convert to JSON string and then to bytes
    pack_mcmeta_content = json.dumps(pack_data, indent=4).encode('utf-8')
    # Add to src_files
    src_files[pack_mcmeta_path] = pack_mcmeta_content
    verbose_print(f"  Generated new {pack_mcmeta_path} with pack_format {current_format} and description '{pack_description}{check_scale(scale)}")

def create_zip_archive(zip_path, src_files, gen_images, scale, dpi, license_file, allowed_paths, current_format):
    """
    Create the final ready-to-use resourcepack ZIPs.

    Args:
        zip_path (str): Full path to output file
        src_files (dict): Source files to pack
        gen_images (dict): Generated images to pack. Accepts `None`
        dpi (int): DPI value to add for gen_images. Accepts `None`
        license_file (bool): Toggle whether to look for and include a license file
        allowed_paths (list): List of paths relative to `src_files` to allow
        current_format (int): Format number for logging purposes
    Returns:
        (bool): True if a zip was created or --dry-run is flagged
    """
    if args.dry_run:
        verbose_print(f"\nDry run enabled, skipping creation of ZIP: {zip_path}")
        return True

    verbose_print(f"\nCreating ZIP archive: {zip_path}")
    created_files = 0

    try:
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    except OSError as e:
        record_error(51, "directory_creation_error", f"Failed to create directory: {e}")
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
                verbose_print(f"  Added scale_{scale}.png -> pack.png (DPI {dpi})")

            # Add license, if provided
            if license_file and os.path.exists(license_file):
                try:
                    zipf.write(license_file)
                    added_files_in_zip.add(license_file)
                    created_files += 1
                    verbose_print(f"  Added license: {license_file}")
                except Exception as e:
                    record_error(53, "license_read_error", f"Failed to read license file: {license_file}: {str(e)}")

            # Include files from src_files
            for rel_path, data in src_files.items():
                # Check if path matches any allowed_path prefix
                if any(rel_path.startswith(p) or rel_path == p for p in allowed_paths):
                    try:
                        zipf.writestr(rel_path, data)
                        added_files_in_zip.add(rel_path)
                        created_files += 1
                        very_verbose_print(f"  Added file to ZIP: {rel_path}")
                    except Exception as e:
                        record_error(None, "zip_write_error", f"Error writing file {rel_path} to ZIP: {str(e)}")

            # Add generated PNGs for the current DPI
            if dpi is not None:
                if dpi in gen_images:
                    for rel_path, data in gen_images[dpi].items():
                        # Check if path matches any allowed_path prefix for generated PNGs
                        if any(rel_path.startswith(p) or rel_path == p for p in allowed_paths):
                            if rel_path in added_files_in_zip:
                                record_error(None, "duplicate_png", f"Attempted to add already-existing PNG to ZIP (DPI {dpi})\n⤷ Path: {rel_path}")
                                continue # Skip adding the duplicate
                            try:
                                zipf.writestr(rel_path, data)
                                added_files_in_zip.add(rel_path)
                                created_files += 1
                                very_verbose_print(f"  Added gen. PNG to ZIP (DPI {dpi}): {rel_path}")
                            except Exception as e:
                                record_error(None, "zip_write_error", f"Error writing generated PNG to ZIP: {str(e)}\n⤷ Path: {rel_path}")

        if created_files > 0:
            proc_stats['talley']['archives_created'] += 1

        verbose_print(f"  Total files added to ZIP: {created_files}")
        return True

    except Exception as e:
        record_error(None, "zip_creation_error", f"Error creating ZIP: {e}")
        return False

def main():
    quiet_print(f"{script_name} {script_ver}")
    quiet_print("Starting pack generation pipeline...")

    ( # Load config
        pack_name,
        pack_description,
        source_dir,
        output_dir,
        license_file,
        allowed_paths,
        formats,
        svg_process_toggle,
        scales_from_config,
        theme_dir,
        default_colors
    ) = load_config(config_file)

    # Validate formats
    if args.format:
        if not args.format in formats:
          record_error(21, "format_not_found", f"Specified format: {args.format} not present in {config_file} 'formats'")

    # Validate license, if provided
    if license_file:
        if not os.path.exists(license_file):
            record_error(52, "license_not_found", f"License file does not exist: {license_file}")

    # Filter scales_from_config and check if args.scale is valid
    if args.scale is not None and svg_process_toggle:
        if args.scale in scales_from_config:
            dpi_values_to_process = {args.scale: scales_from_config[args.scale]}
            quiet_print(f"\nGenerating only for scale {args.scale} ({scales_from_config[args.scale]} DPI)")
        else:
            record_error(22, "scale_not_found", f"Specified scale '{args.scale}' not found in buildcfg.json")

    else:
        dpi_values_to_process = scales_from_config

    # src_files will be populated with the original `./src` tree.
    src_files = scan_src_files(source_dir)
    # gen_images will be populated later by PNGs generated from SVGs, with the root keys as DPI.
    gen_images = defaultdict(dict)

    # SVG editing and PNG generation
    if svg_process_toggle == True:
        gen_images = defaultdict(dict)
        verbose_print("\nProcessing SVG files...")
        svg_files_processed = 0

        # Apply theme to all SVG files in src_files
        src_files = apply_theme(
            src_files,
            theme_dir,
            args.theme,
            default_colors
        )

        # Iterate over a copy of keys because we'll be modifying src_files
        gen_images = convert_svg_to_png(
            src_files,
            dpi_values_to_process
        )

    # Process formats and create ZIPs
    quiet_print("\nProcessing formats and creating ZIP archives...")

    for current_format in sorted(formats.keys(), reverse=True):
        # Break loop if current `current_format` is lower than `args.format` (Pack would have been created by the previous loop)
        if args.format is not None and current_format < args.format:
            verbose_print(f"\nEnding processing as current format {current_format} is lower than specified --format-key {args.format}")
            break

        proc_stats['talley']['formats_processed'] += 1

        verbose_print(f"\nProcessing format: {current_format}")

        # Check for and process a format-specific .json file in `./src`
        # with an "exclusions" list.
        src_files, gen_images = apply_exclusions(
            current_format,
            source_dir,
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
            verbose_print(f"Skipping .zip creation of format: {current_format} (not the specified --format-key)")
            continue

        # Only create per-scale packs if svg_process_toggle is True
        if svg_process_toggle == True:
            for scale, dpi in dpi_values_to_process.items():
                generate_pack_mcmeta(current_format, formats, pack_description, scale, src_files)

                zip_name = f"{pack_name}-{args.packver}-{formats[current_format]}-scale-{scale}.zip"
                zip_path = os.path.join(output_dir, str(current_format), zip_name)
                create_zip_archive(
                    zip_path,
                    src_files,
                    gen_images,
                    scale,
                    dpi,
                    license_file,
                    allowed_paths,
                    current_format
                )
        else: # Regular pack creation
            generate_pack_mcmeta(current_format, formats, pack_description, None, src_files)

            zip_name = f"{pack_name}-{args.packver}-{formats[current_format]}.zip"
            zip_path = os.path.join(output_dir, zip_name)
            create_zip_archive(
                zip_path,
                src_files,
                None,
                None,
                None,
                license_file,
                allowed_paths,
                current_format
            )

    quiet_print("\nDone!")
    if not args.dry_run:
        quiet_print("Output available in ./generated")
    else:
        quiet_print("No files created (--dry-run)")

    # Print final summary
    print_summary()

if __name__ == "__main__":
    main()
