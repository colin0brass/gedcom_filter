# gedcom_filter

A Python toolkit for parsing, filtering, and exporting GEDCOM genealogical data with advanced features for photo management, relationship filtering, and custom output.

## Features
- Parse GEDCOM files and extract individuals, families, and events
- Filter by ancestor/descendant generations, partners, siblings, and more
- Export filtered GEDCOM files with correct FAMS/FAMC mapping
- Copy and reference photo files in output
- Command-line interface with verbose/debug logging

## Usage

### Command-Line Example
```
python gedcom_filter.py <input.ged> [options]
```


#### Common Options
- `--ancestor_generations N`   : Include N generations of ancestors (use negative for all)
- `--descendant_generations N` : Include N generations of descendants
- `--wider_descendants_mode {none,start,deep}` : Control inclusion of wider descendants:
	- `none` (default): Do not include wider descendants
	- `start`: Include other descendants of ancestors down to the starting generation
	- `deep`: Include other descendants of ancestors down to the descendants level
- `--partners`                 : Include partners of filtered individuals
- `--siblings`                 : Include siblings of filtered individuals
- `--only_use_photo_tags`      : Only use photo tags for photo extraction
- `--output_file FILE`         : Output GEDCOM file name
- `--photo_dir DIR`            : Directory to copy photos to
- `--verbose`                  : Enable debug logging
- `--help`                     : Show help message


### Example
```
python gedcom_filter.py mytree.ged --ancestor_generations 3 --descendant_generations 1 --wider_descendants_mode start --partners --output_file filtered.ged --photo_dir photos --verbose
```

## Project Structure
- `gedcom_filter.py`   : Main CLI entry point
- `gedcom_parser.py`   : GEDCOM parsing, filtering, and writing logic
- `gedcom.py`          : Core data structures and filtering helpers
- `Person.py`          : Person and LifeEvent classes
- `location.py`        : Location/geocoding utilities
- `LatLon.py`          : Latitude/longitude helpers
- `addressbook.py`     : Fuzzy address book for place matching

## Requirements
- Python 3.8+
- [ged4py](https://pypi.org/project/ged4py/)

Install dependencies:
```
pip install -r requirements.txt
```

## Author
Colin Osborne (@colin0brass)

## License
MIT License
