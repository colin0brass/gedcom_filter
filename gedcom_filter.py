"""
gedcom_filter.py - Main entry point for GEDCOM filtering and export.

Processes GEDCOM files, filters people by generations, manages geocoding, and exports filtered GEDCOM and summary files.

Workflow:
    1. Parse command-line arguments for input files, output folder, and options.
    2. For each GEDCOM file:
        - Resolve file paths and output locations.
        - Parse and correct GEDCOM file structure if needed.
        - Filter people by ancestor/descendant generations, partners, siblings, etc.
        - Geocode places using OpenStreetMap/Nominatim, with caching and fuzzy matching.
        - Optionally use alternative place/address files for improved geocoding.
        - Save updated geocoding cache.
        - Export filtered GEDCOM, summary CSVs, and KML for Google Earth.
        - Generate birth/death country heatmaps and other visualizations.
    3. All output files are saved in the specified output folder.

Author: @colin0brass
Last updated: 2025-11-29
"""

import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union, List

from gedcom import Gedcom

def get_arg_parser() -> argparse.ArgumentParser:
    """
    Create and return the argument parser for the CLI.

    Returns:
        argparse.ArgumentParser: Configured argument parser with all supported options for filtering and exporting GEDCOM data.
    """
    parser = argparse.ArgumentParser(
        description='Convert GEDCOM to KML and lookup addresses',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('input_files', type=str, nargs='+',
        help='One or more GEDCOM files to process')
    parser.add_argument('--only_use_photo_tags', action='store_true',
        help='Only use _PHOTO tags for photos, ignore OBJE tags')
    parser.add_argument('--verbose', action='store_true',
        help='Enable verbose output')
    parser.add_argument('--output_folder', type=str, default='output',
        help='Folder to put output files (default: ./output)')
    parser.add_argument('--output_file', type=str, default=None,
        help='Output GEDCOM file name (default: derived from input file)')
    parser.add_argument('--ancestor_generations', type=int, default=2,
        help='Number of ancestor generations to include in filtered GEDCOM (default: 2; -1 for all ancestors)')
    parser.add_argument('--descendant_generations', type=int, default=2,
        help='Number of descendant generations to include in filtered GEDCOM (default: 2; -1 for all descendants)')
    parser.add_argument('--start_person', type=str, default="David Leonard Osborne",
        help='Name of the starting person to filter generations from (default: "David Leonard Osborne")')
    parser.add_argument('--wider_descendants_mode', type=str, choices=[
        'none', 'start', 'deep'], default='none',
        help='Control inclusion of wider descendants: "none" (default), "start" (to starting generation), or "deep" (to descendants level)')
    parser.add_argument('--partners', action='store_true',
        help='Include partners of ancestors in the filtered GEDCOM')
    parser.add_argument('--siblings', action='store_true',
        help='Include siblings of ancestors in the filtered GEDCOM')
    return parser

def main() -> None:
    """
    Main entry point for the GEDCOM filter script.

    Parses command-line arguments, configures logging, processes GEDCOM files, and generates filtered output files and reports.

    Workflow:
      1. Parse CLI arguments (input files, output folder, verbosity, filtering options)
      2. Configure logging based on verbose flag
      3. Create output folder if it doesn't exist
      4. For each input GEDCOM file, parse, filter, geocode, and export results
      5. Save filtered GEDCOM, summary CSVs, and optional KML/visualizations
    """
    import sys
    parser = get_arg_parser()
    # Print help if no arguments or only --help is provided
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ('-h', '--help')):
        parser.print_help(sys.stderr)
        sys.exit(0)
    try:
        args = parser.parse_args()
    except SystemExit:
        parser.print_help(sys.stderr)
        sys.exit(1)
    if not args.input_files:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Configure logging before any logging calls
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s'
    )

    global logger
    logger = logging.getLogger(__name__)

    # Print a compact summary of the program arguments
    arg_summary = ', '.join(f"{k}={v}" for k, v in vars(args).items())
    print(f"Program arguments: {arg_summary}")

    script_dir = Path(__file__).parent.resolve()

    output_folder = Path(args.output_folder).resolve()
    output_folder.mkdir(parents=True, exist_ok=True)

    wider_descendants_end_generation: Union[int, None] = None
    if args.wider_descendants_mode == 'none':
        wider_descendants_end_generation = None
    elif args.wider_descendants_mode == 'deep':
        wider_descendants_end_generation = args.descendant_generations
    elif args.wider_descendants_mode == 'start':
        wider_descendants_end_generation = 0

    for gedcom_file in args.input_files:
        # Support gedcom_file as absolute or relative path
        input_path = Path(gedcom_file)
        if not input_path.is_absolute():
            input_path = (Path.cwd() / input_path).resolve()
        base_file_name = input_path.stem

        logger.info(f'Processing GEDCOM file: {gedcom_file}')
        my_gedcom = Gedcom(
            gedcom_file=input_path.resolve(),
            only_use_photo_tags=args.only_use_photo_tags
        )

        starting_person_id = my_gedcom.find_person_by_name(args.start_person)
        logger.info(f"Starting person ID(s): {starting_person_id[0]}")

        logger.info("Filtering relatives...")
        people_list, message = my_gedcom.filter_generations(
            starting_person_id=starting_person_id[0],
            num_ancestor_generations=args.ancestor_generations,
            num_descendant_generations=args.descendant_generations,
            wider_descendants_end_generation=wider_descendants_end_generation,
            include_partners=args.partners,
            include_siblings=args.siblings
        )
        print(message)
        
        output_filename = args.output_file if args.output_file else f"{base_file_name}_filtered.ged"
        if not str(output_filename).lower().endswith('.ged'):
            output_filename = f"{output_filename}.ged"
        logger.info(f"Exporting filtered GEDCOM with photos to: {output_folder / output_filename}")
        my_gedcom.export_people_with_photos(
            people = people_list,
            new_gedcom_path = output_folder / output_filename,
            photo_dir = output_folder / "photos"
        )
        print(f"Filtered GEDCOM exported to: {output_folder / output_filename}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)