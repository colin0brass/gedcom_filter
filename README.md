# gedcom_filter

A Python toolkit for parsing, filtering, and exporting GEDCOM genealogical data with advanced features for photo management, relationship filtering, and custom output.

See also: [geo_gedcom module README](geo_gedcom/README.md)

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
- `geo_gedcom/gedcom_parser.py`   : GEDCOM parsing, filtering, and writing logic
- `geo_gedcom/gedcom.py`          : Core data structures and filtering helpers
- `geo_gedcom/person.py`          : Person and LifeEvent classes
- `geo_gedcom/location.py`        : Location/geocoding utilities
- `geo_gedcom/lat_lon.py`         : Latitude/longitude helpers
- `geo_gedcom/addressbook.py`     : Fuzzy address book for place matching
- `geo_gedcom/gedcom_date.py`     : Date parsing and normalization

## Requirements

- Python 3.8+
- [ged4py](https://pypi.org/project/ged4py/)
- [rapidfuzz](https://pypi.org/project/rapidfuzz/)

Install dependencies:
```
pip install -r requirements.txt
```

## Testing
Test coverage is provided for all major modules and real-world GEDCOM scenarios.
Run tests with:
```
pytest
```


## Author
Colin Osborne (@colin0brass)

## License
MIT License
