"""
gedcom_parser.py - GEDCOM parsing and export utilities.

Defines the GedcomParser class for parsing GEDCOM files, extracting people and places, copying photo files, and exporting filtered GEDCOM data.
Supports robust handling of INDI/FAM records, photo management, and geocoding integration.

Author: @colin0brass
Last updated: 2025-11-29
"""
import os
import re
from typing import Dict, List, Optional
import tempfile

import logging
from pathlib import Path

from ged4py.parser import GedcomReader
from ged4py.model import Record, NameRec
from ged4py.date import DateValue

from location import Location
from LatLon import LatLon
from Person import Person, LifeEvent
from addressbook import FuzzyAddressBook

logger = logging.getLogger(__name__)

class GedcomParser:
    """
    Parses GEDCOM files and extracts people and places.

    Attributes:
        gedcom_file (Optional[str]): Path to GEDCOM file.
    """
    __slots__ = [
        'gedcom_file',
        '_cached_people', '_cached_address_book',
        'only_use_photo_tags'
    ]

    LINE_RE = re.compile(
        r'^(\d+)\s+(?:@[^@]+@\s+)?([A-Z0-9_]+)(.*)$'
    )  # allow optional @xref@ before the tag

    def __init__(self, gedcom_file: Path = None, only_use_photo_tags: bool = True) -> None:
        """
        Initialize GedcomParser.

        Args:
            gedcom_file (Path): Path to GEDCOM file.
        """
        self.gedcom_file = self.check_fix_gedcom(gedcom_file)
        # caches populated by _load_people_and_places()
        self._cached_people = None
        self._cached_address_book = None
        self.only_use_photo_tags = only_use_photo_tags

    def close(self):
        """Placeholder for compatibility."""
        pass

    def check_fix_gedcom(self, input_path: Path) -> Path:
        """Fixes common issues in GEDCOM records."""
        temp_fd, temp_path = tempfile.mkstemp(suffix='.ged')
        os.close(temp_fd)
        changed = self.fix_gedcom_conc_cont_levels(input_path, temp_path)
        if changed:
            logger.warning(f"Checked and made corrections to GEDCOM file '{input_path}' saved as {temp_path}")
        return temp_path if changed else input_path

    def fix_gedcom_conc_cont_levels(self, input_path: Path, temp_path: Path) -> bool:
        """
        Fixes GEDCOM continuity and structure levels.
        These types of GEDCOM issues have been seen from Family Tree Maker exports.
        If not fixed, they can cause failure to parse the GEDCOM file correctly.
        """

        cont_level = None
        changed = False

        try:
            with open(input_path, 'r', encoding='utf-8', newline='', errors="replace") as infile, \
                open(temp_path, 'w', encoding='utf-8', newline='') as outfile:
                for raw in infile:
                    line = raw.rstrip('\r\n')
                    m = self.LINE_RE.match(line)
                    if not m:
                        outfile.write(raw)
                        continue

                    level_s, tag, rest = m.groups()
                    level = int(level_s)

                    if tag in ('CONC', 'CONT'):
                        fixed_level = cont_level if cont_level is not None else level
                        outfile.write(f"{fixed_level} {tag}{rest}\n")
                        if fixed_level != level:
                            changed = True
                    else:
                        cont_level = level + 1
                        outfile.write(raw)
        except IOError as e:
            logger.error(f"Failed to fix GEDCOM file {input_path}: {e}")
        return changed

    @staticmethod
    def get_place(record: Record, placetag: str = 'PLAC') -> Optional[str]:
        """
        Extracts the place value from a record.

        Args:
            record (Record): GEDCOM record.
            placetag (str): Tag to extract.

        Returns:
            Optional[str]: Place value or None.
        """
        place_value = None
        if record:
            place = record.sub_tag(placetag)
            if place:
                place_value = place.value
        return place_value
    
    def __get_event_location(self, record: Record) -> Optional[LifeEvent]:
        """
        Creates a LifeEvent from a record.

        Args:
            record (Record): GEDCOM record.

        Returns:
            Optional[LifeEvent]: LifeEvent object or None.
        """
        event = None
        if record:
            place = GedcomParser.get_place(record)
            event = LifeEvent(place, record.sub_tag('DATE'), record=record)
        return event

    def __create_person(self, record: Record) -> Person:
        """
        Creates a Person object from a record.

        Args:
            record (Record): GEDCOM record.

        Returns:
            Person: Person object.
        """
        global BackgroundProcess

        person = Person(record.xref_id)
        person.name = ''
        name: NameRec = record.sub_tag('NAME')
        if name:
            person.firstname = record.name.first
            person.surname = record.name.surname
            person.maidenname = record.name.maiden
            person.name = f'{record.name.format()}'
        if person.name == '':
            person.firstname = 'Unknown'
            person.surname = 'Unknown'
            person.maidenname = 'Unknown'
            person.name = 'Unknown'
        person.sex = record.sex
        person.birth = self.__get_event_location(record.sub_tag('BIRT'))
        person.death = self.__get_event_location(record.sub_tag('DEAT'))
        title = record.sub_tag("TITL")
        person.title = title.value if title else ""

        # Grab photos
        photos_all, preferred_photos = self._extract_photos_from_record(record)
        person.photos_all = photos_all
        if preferred_photos:
            person.photo = preferred_photos[0]
        elif photos_all:
            person.photo = photos_all[0]
        else:
            person.photo = None

        return person

    def _extract_photos_from_record(self, record: Record) -> list:
        """
        Extracts all valid photo file paths from a GEDCOM record.

        Args:
            record (Record): GEDCOM record.
        """
        photos = []
        preferred_photos = []
        # MyHeritage and possibly others use _PHOTO tag for preferred photos
        for obj in record.sub_tags("_PHOTO"):
            files, _ = self._extract_photo(obj)
            preferred_photos.extend(files)
        if not self.only_use_photo_tags:
            # Standard OBJE tags, possibly with "_PRIM" sub-tag for preferred photos
            for obj in record.sub_tags("OBJE"):
                files, preferred_files = self._extract_photo(obj)
                photos.extend(files)
                preferred_photos.extend(preferred_files)
        return photos, preferred_photos
    
    def _extract_photo(self, obj: Record) -> list:
        """
        Extracts all valid photo file paths from a GEDCOM record's OBJE tags.

        Args:
            record (Record): GEDCOM record.

        Returns:
            list: List of valid photo file paths (strings).
        """
        allowed_exts = {'jpg', 'jpeg', 'bmp', 'png', 'gif'}
        photos = []
        preferred_photos = []
        file_tag = obj.sub_tag("FILE")
        if file_tag:
            file_value = file_tag.value
            ext = file_value.lower().split('.')[-1]
            form_tags = [t for t in obj.sub_tags("FORM") if t.value]
            form_exts = [form_tag.value.lower() for form_tag in form_tags]
            if ext in allowed_exts or any(f in allowed_exts for f in form_exts):
                photos.append(file_value)
                prim_tag = obj.sub_tag("_PRIM")
                if prim_tag and prim_tag.value.upper() != 'N':
                    preferred_photos.append(file_value)

        return photos, preferred_photos
    
    def __create_people(self, records0) -> Dict[str, Person]:
        """
        Creates a dictionary of Person objects from records.

        Args:
            records0: GEDCOM records.

        Returns:
            Dict[str, Person]: Dictionary of Person objects.
        """
        people = {}
        for record in records0('INDI'):
            people[record.xref_id] = self.__create_person(record)
        return people

    def __add_marriages(self, people: Dict[str, Person], records) -> Dict[str, Person]:
        """
        Adds marriages and parent/child relationships to people.

        Args:
            people (Dict[str, Person]): Dictionary of Person objects.
            records: GEDCOM records.

        Returns:
            Dict[str, Person]: Updated dictionary of Person objects.
        """
        idx = 0
        for record in records('FAM'):
            husband_record = record.sub_tag('HUSB')
            wife_record = record.sub_tag('WIFE')
            husband = people.get(husband_record.xref_id) if husband_record else None
            wife = people.get(wife_record.xref_id) if wife_record else None
            # Add partners (irrespective of marriages)
            if husband and wife:
                husband.partners.append(wife_record.xref_id)
                wife.partners.append(husband_record.xref_id)
            # Add marriage events
            for marriages in record.sub_tags('MARR'):
                marriage_event = self.__get_event_location(marriages)
                if husband:
                    # add missing xref_id to marriage event record for later use
                    # BUG this causes the xref_id to be overwritten sometime between husband and wife processing
                    # marriage_event.record.xref_id = wife_record.xref_id if wife_record else None
                    husband.marriages.append(marriage_event)
                if wife:
                    # marriage_event.record.xref_id = husband_record.xref_id if husband_record else None
                    wife.marriages.append(marriage_event)
            for child in record.sub_tags('CHIL'):
                if child.xref_id in people:
                    if people[child.xref_id]:
                        if husband:
                            people[child.xref_id].father = husband.xref_id
                            husband.children.append(child.xref_id)
                        if wife:
                            people[child.xref_id].mother = wife.xref_id
                            wife.children.append(child.xref_id)
            idx += 1
        return people

    def parse_people(self) -> Dict[str, Person]:
        """
        Parses people from the GEDCOM file.

        Returns:
            Dict[str, Person]: Dictionary of Person objects.
        """
        if self._cached_people:
            return self._cached_people
        self._load_people_and_places()
        return self._cached_people if self._cached_people else {}

    def _fast_count(self):
        def _count_gedcom_records( path, encoding):
                """Return (people, families) counts for a GEDCOM file with given encoding."""
                people = families = 0
                with open(path, encoding=encoding) as f:
                    for line in f:
                        if line.startswith("0 @") and " INDI" in line:
                            people += 1
                        elif line.startswith("0 @") and " FAM" in line:
                            families += 1
                return people, families

        encodings = ["utf-8", "latin-1"]  # try in order
        for enc in encodings:
            try:
                people, families = _count_gedcom_records(str(self.gedcom_file), enc)
                logger.info(f"Fast count people {people} & families {families}")
                return
            except UnicodeDecodeError:
                # try next encoding
                continue
            except Exception as e:
                logger.error(
                    f"Error fast counting people and families from GEDCOM file '{self.gedcom_file}' with encoding {enc}: {e}"
                )
                return
        # If we get here, all encodings failed
        logger.error(f"Could not decode GEDCOM file '{self.gedcom_file}' with any known encoding")

    def _load_people_and_places(self):
        """
        Loads people and places from the GEDCOM file.
        """

        try:
            # Single pass: build people and then addresses
            with GedcomReader(str(self.gedcom_file)) as g:
                records = g.records0
                self._cached_people = self.__create_people(records)
                self._cached_people = self.__add_marriages(self._cached_people, records)

                # Now extract places
                # (considered to extract from people, however suspect that might risk missing some record types)
                self._cached_address_book = FuzzyAddressBook()
                for indi in records('INDI'):
                    for ev in indi.sub_records:
                        plac = ev.sub_tag_value("PLAC")
                        if plac:
                            place = plac.strip()
                            self._cached_address_book.fuzzy_add_address(place, None)

                for fam in records('FAM'):
                    for ev in fam.sub_records:
                        plac = ev.sub_tag_value("PLAC")
                        if plac:
                            place = plac.strip()
                            self._cached_address_book.fuzzy_add_address(place, None)

        except Exception as e:
            logger.error(f"Error extracting people & places from GEDCOM file '{self.gedcom_file}': {e}")

    def get_full_address_book(self) -> FuzzyAddressBook:
        """
        Returns address book of all places found in the GEDCOM file.

        Returns:
            FuzzyAddressBook: Address book of places.
        """

        # Return cached if available
        if self._cached_address_book:
            return self._cached_address_book
        self._load_people_and_places()
        return self._cached_address_book if self._cached_address_book else FuzzyAddressBook()

    def gedcom_writer(self, people, output_path, photo_dir=None):
        """
        Write a GEDCOM file from a dictionary of Person objects.

        Args:
            people (Dict[str, Person]): Dictionary of Person objects to write.
            output_path (Path): Path to write the GEDCOM file.
            photo_dir (Optional[Path]): If provided, copy photo files to this directory and update references.
        """
        import shutil
        if photo_dir:
            photo_dir.mkdir(parents=True, exist_ok=True)
            photo_relative_folder_path = os.path.relpath(photo_dir, start=os.path.dirname(output_path))
        else:
            photo_relative_folder_path = None

        # Build FAM records and FAMS/FAMC mapping
        fam_map = {}  # (father, mother) -> set(children)
        # 1. Add families with children (traditional FAMs)
        for person in people.values():
            father = getattr(person, 'father', None)
            mother = getattr(person, 'mother', None)
            partners = getattr(person, 'partners', [])
            if father not in people:
                father = None
            if mother not in people:
                mother = None
            if father or mother:
                fam_key = (str(father) if father else '', str(mother) if mother else '')
                if fam_key not in fam_map:
                    fam_map[fam_key] = set()
                fam_map[fam_key].add(person.xref_id)

        # 2. Add partner-only families (no children)
        partner_fam_keys = set()
        for person in people.values():
            partners = getattr(person, 'partners', [])
            for partner_id in partners:
                if partner_id in people:
                    # Always order tuple to avoid duplicates (A,B) and (B,A)
                    key = tuple(sorted([person.xref_id, partner_id]))
                    # Skip if this pair already has a family with children
                    fam_key1 = (person.xref_id, partner_id)
                    fam_key2 = (partner_id, person.xref_id)
                    if fam_key1 in fam_map or fam_key2 in fam_map:
                        continue
                    if key not in partner_fam_keys:
                        partner_fam_keys.add(key)
                        fam_map[key] = set()  # No children


        fam_id_map = {}
        fam_count = 1
        for fam_key in fam_map:
            fam_id = f"@F{fam_count:04d}@"
            fam_id_map[fam_key] = fam_id
            fam_count += 1

        # Assign FAMS (as spouse) and FAMC (as child) to each person
        for fam_key, fam_id in fam_id_map.items():
            # fam_key is either (father, mother) or (partner1, partner2) for partner-only fams
            if len(fam_key) == 2:
                a, b = fam_key
                children = fam_map[fam_key]
                # FAMS: assign to both partners if both exist
                if a and a in people:
                    if not hasattr(people[a], 'family_spouse'):
                        people[a].family_spouse = []
                    people[a].family_spouse.append(fam_id)
                if b and b in people:
                    if not hasattr(people[b], 'family_spouse'):
                        people[b].family_spouse = []
                    people[b].family_spouse.append(fam_id)
                # FAMC: assign to children (if any)
                for child in children:
                    if child in people:
                        if not hasattr(people[child], 'family_child'):
                            people[child].family_child = []
                        people[child].family_child.append(fam_id)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("0 HEAD\n")
            f.write("1 SOUR gedcom_filter\n")
            f.write("1 GEDC\n2 VERS 5.5.1\n")
            f.write("1 CHAR UTF-8\n")
            # Write INDI records
            for person in people.values():
                self._write_person_gedcom(f, person, photo_dir, photo_relative_folder_path)
            # Write FAM records
            for fam_key, children in fam_map.items():
                fam_id = fam_id_map[fam_key]
                self._write_family_gedcom(f, fam_id, fam_key, children)
            f.write("0 TRLR\n")

    def _write_person_gedcom(self, f, person, photo_dir, photo_relative_folder_path):
        import shutil
        f.write(f"0 {person.xref_id} INDI\n")
        if person.name:
            f.write(f"1 NAME {person.name}\n")
        if person.sex:
            f.write(f"1 SEX {person.sex}\n")
        if person.birth:
            f.write("1 BIRT\n")
            if person.birth.date:
                f.write(f"2 DATE {person.birth.date.value}\n")
            if person.birth.place:
                f.write(f"2 PLAC {person.birth.place}\n")
        if person.death:
            f.write("1 DEAT\n")
            if person.death.date:
                f.write(f"2 DATE {person.death.date.value}\n")
            if person.death.place:
                f.write(f"2 PLAC {person.death.place}\n")
        # Write FAMS (spouse family) and FAMC (child family)
        for fams in getattr(person, 'family_spouse', []):
            f.write(f"1 FAMS {fams}\n")
        for famc in getattr(person, 'family_child', []):
            f.write(f"1 FAMC {famc}\n")
        # Write photo if present
        if person.photo:
            src_photo = Path(person.photo)
            dest_photo = src_photo
            if photo_dir:
                dest_photo = photo_dir / src_photo.name
                try:
                    shutil.copy2(src_photo, dest_photo)
                except Exception as e:
                    logger.warning(f"Could not copy photo {src_photo} to {dest_photo}: {e}")
            if photo_relative_folder_path:
                file_path = f"{photo_relative_folder_path}/{dest_photo.name}"
            else:
                file_path = str(dest_photo)
            f.write("1 OBJE\n")
            f.write(f"2 FILE {file_path}\n")
            ext = dest_photo.suffix[1:].lower()
            if ext:
                f.write(f"2 FORM {ext}\n")

    def _write_family_gedcom(self, f, fam_id, fam_key, children):
        father, mother = fam_key
        f.write(f"0 {fam_id} FAM\n")
        if father:
            f.write(f"1 HUSB {father}\n")
        if mother:
            f.write(f"1 WIFE {mother}\n")
        for child in children:
            f.write(f"1 CHIL {child}\n")