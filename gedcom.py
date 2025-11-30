"""
gedcom.py - Main GEDCOM data model and handler.

This module defines the Gedcom class, which provides high-level operations for parsing,
filtering, and exporting GEDCOM genealogical data. It supports:
    - Loading and parsing GEDCOM files
    - Filtering ancestors and descendants by generation
    - Searching for people by name
    - Exporting filtered people and associated photos to new GEDCOM files
    - Integrating with geolocation and address book utilities

Author: @colin0brass
Last updated: 2025-11-29
"""

from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union


from addressbook import FuzzyAddressBook
from gedcom_parser import GedcomParser
from Person import Person, LifeEvent

logger = logging.getLogger(__name__)

class Gedcom:
    """
    Main GEDCOM handler for people and places.

    Provides high-level operations for parsing, filtering, and exporting GEDCOM genealogical data.

    Attributes:
        gedcom_parser (GedcomParser): Instance for parsing GEDCOM files and extracting data.
        people (Dict[str, Person]): Dictionary of all Person objects indexed by xref_id.
        address_book (FuzzyAddressBook): Address book of all places found in the GEDCOM file.
    """
    __slots__ = [
        'gedcom_parser',
        'people',
        'address_book'
    ]
    def __init__(self, gedcom_file: Path, only_use_photo_tags: bool) -> None:
        """Initialize the Gedcom handler and load people and places from the GEDCOM file."""
        self.gedcom_parser = GedcomParser(
            gedcom_file=gedcom_file,
            only_use_photo_tags=only_use_photo_tags
        )
        self.people = {}
        self.address_book = FuzzyAddressBook()

        self._parse_people()

    def close(self):
        """
        Close the GEDCOM parser and release any resources.
        """
        self.gedcom_parser.close()

    def _parse_people(self) -> Dict[str, Person]:
        """
        Parse people from the GEDCOM file and populate the people dictionary.

        Returns:
            Dict[str, Person]: Dictionary of Person objects indexed by xref_id.
        """
        self.people = self.gedcom_parser.parse_people()
        return self.people

    def get_full_address_book(self) -> FuzzyAddressBook:
        """
        Get all places from the GEDCOM file as a FuzzyAddressBook.

        Returns:
            FuzzyAddressBook: Address book containing all unique places.
        """
        self.address_book = self.gedcom_parser.get_full_address_book()
        return self.address_book

    def filter_generations(self, starting_person_id: str, num_ancestor_generations: int, num_descendant_generations: int, include_wider_descendants: bool, include_partners: bool = False, include_siblings: bool = False) -> Dict[str, Person]:
        """
        Filter people to include ancestors and descendants of a starting person.

        Traverses the family tree starting from a given person, going back a specified
        number of generations to collect ancestors, then forward the same number of
        generations to collect descendants. Optionally includes partners.

        Args:
            starting_person_id (str): The xref_id of the starting person.
            num_generations (int): Number of generations to include in each direction.
            include_descendants (bool): Whether to include descendants in the result.
            include_partners (bool): Whether to include partners of collected individuals.

        Returns:
            Dict[str, Person]: Dictionary of filtered Person objects including the starting
                person, their ancestors, and optionally descendants and partners.

        Raises:
            ValueError: If starting_person_id is not found in the people dictionary.
        """
        if starting_person_id not in self.people:
            raise ValueError(f"Person with ID '{starting_person_id}' not found in GEDCOM data")

        class person_gen:
            def __init__(self, person_id: str, generation: int):
                self.person_id = person_id
                self.generation = generation

        class people_gen_list:
            def __init__(self):
                self.people_gen: List[person_gen] = []
                self.earliest_generation = 0
                self.latest_generation = 0
            def add(self, person_id: str, generation: int):
                self.people_gen.append (person_gen (person_id, generation))
                if generation < self.earliest_generation:
                    self.earliest_generation = generation
                if generation > self.latest_generation:
                    self.latest_generation = generation
            @property
            def num_generations(self) -> int:
                return self.latest_generation - self.earliest_generation + 1
            def get_generation(self, generation: int) -> List[str]:
                r = []
                for pg in self.people_gen:
                    if pg.generation == generation:
                        r.append (pg.person_id)
                return r
            def exists(self, person_id: str) -> bool:
                for pg in self.people_gen:
                    if pg.person_id == person_id:
                        return True
                return False
            def all(self) -> Dict[str, int]:
                """
                Return a dict mapping person_id to generation for all unique person_ids.
                """
                result = {}
                for pg in self.people_gen:
                    if pg.person_id not in result:
                        result[pg.person_id] = pg.generation
                return result
            
        filtered_people_generations = people_gen_list()

        # generation will be 0 for starting person, negative for ancestors, positive for descendants
        
        def add_partners(person_id: str, generation: int):
            """Add partners and siblings of a person."""
            try:
                person = self.people[person_id]
                # Include partners if requested
                for partner in person.partners:
                    partner_id = partner.xref_id if hasattr(partner, 'xref_id') else partner
                    if not filtered_people_generations.exists(partner_id):
                        logger.info(f"Gen {generation}: Collecting partner: {partner_id}: {self.people[partner_id].name if partner_id in self.people else partner_id}")
                        filtered_people_generations.add(partner_id, generation)
            except:
                logger.warning(f"Person ID '{person_id}' not found while adding partners")
                return
            
        def add_siblings(person_id: str, generation: int):
            """Add siblings of a person."""
            try:
                person = self.people[person_id]
                # Include siblings if requested
                if person.father and person.mother:
                    father = person.father.xref_id if hasattr(person.father, 'xref_id') else person.father
                    mother = person.mother.xref_id if hasattr(person.mother, 'xref_id') else person.mother
                    siblings_list = set()
                    siblings_list.update(self.people[father].children if father in self.people else [])
                    siblings_list.update(self.people[mother].children if mother in self.people else [])
                    for sibling_id in siblings_list:
                        if sibling_id != person_id:
                            if not filtered_people_generations.exists(sibling_id):
                                logger.info(f"Gen {generation}: Collecting sibling: {sibling_id}: {self.people[sibling_id].name if sibling_id in self.people else sibling_id}")
                                filtered_people_generations.add(sibling_id, generation)
            except:
                logger.warning(f"Person ID '{person_id}' not found while adding siblings")
                return
            
        # First, collect ancestors going back
        def collect_ancestors(person_id: str, generation: int):
            """Recursively collect ancestors. Negative generation = earlier (ancestors)."""
            if abs(generation) < num_ancestor_generations or num_ancestor_generations == -1:
                is_last_generation = False
            else:
                is_last_generation = True

            try:
                person = self.people[person_id]
                if not filtered_people_generations.exists(person_id):
                    logger.info(f"Gen {generation}: Collecting ancestor: {person_id}: {person.name}")
                    filtered_people_generations.add(person_id, generation)
                if include_partners:
                    add_partners(person_id, generation)
                if include_siblings and not is_last_generation:
                    add_siblings(person_id, generation)
            except:
                logger.warning(f"Person ID '{person_id}' not found while collecting ancestors")
                return

            if not is_last_generation:
                next_generation = generation - 1
                if person.father:
                    collect_ancestors(person.father.xref_id if hasattr(person.father, 'xref_id') else person.father, next_generation)
                if person.mother:
                    collect_ancestors(person.mother.xref_id if hasattr(person.mother, 'xref_id') else person.mother, next_generation)
        
        # Collect ancestors including the starting person
        collect_ancestors(person_id = starting_person_id, generation = 0)
        
        # Now collect descendants going forward from all people we've collected so far
        def collect_descendants(person_id: str, generation: int, end_generation: Union[int, None]):
            """Recursively collect descendants. Positive generation = later (descendants)."""
            if end_generation is None:
                is_last_generation = False
            elif generation < end_generation:
                is_last_generation = False
            else:
                is_last_generation = True

            try:
                if not filtered_people_generations.exists(person_id):
                    logger.info(f"Gen {generation}: Collecting descendant: {person_id}: {self.people[person_id].name if person_id in self.people else person_id}")
                    filtered_people_generations.add(person_id, generation)
                if include_partners:
                    add_partners(person_id, generation)
            except:
                logger.warning(f"Person ID '{person_id}' not found while collecting descendants")
                return

            if not is_last_generation:
                next_generation = generation + 1
                person = self.people[person_id]
                for child_id in person.children:
                    collect_descendants(child_id, next_generation, end_generation=end_generation)
        
        # Collect descendants from each ancestor
        if include_wider_descendants:        
            earliest_gen = filtered_people_generations.earliest_generation
            for generation in range(0, earliest_gen-1, -1):
                person_ids = filtered_people_generations.get_generation(generation)
                for person_id in person_ids:
                    collect_descendants(person_id=person_id, generation=generation,
                                        end_generation=0)

        # Finally, collect descendants from the starting person
        collect_descendants(person_id = starting_person_id, generation = 0,
                            end_generation=num_descendant_generations)

        # Combine all generations into a single dictionary of people
        all_ids = filtered_people_generations.all()
        filtered_people = {person_id: self.people[person_id] for person_id in all_ids}

        earliest_gen = filtered_people_generations.earliest_generation
        latest_gen = filtered_people_generations.latest_generation
        num_generations = latest_gen - earliest_gen + 1
        logger.info(f"Filtered {len(filtered_people)} people from {len(self.people)} total "
                   f"({earliest_gen} earliest to {latest_gen} latest; {num_generations} generations) "
                   f"from person {starting_person_id}: {self.people[starting_person_id].name})")
        
        return filtered_people

    def find_person_by_name(self, name: str, exact_match: bool = False) -> Optional[List[str]]:
        """
        Find person ID(s) by name.

        Searches through all people to find matching names. Can do exact or partial
        (case-insensitive) matching.

        Args:
            name (str): The name to search for.
            exact_match (bool): If True, requires exact match (case-insensitive).
                If False, matches if name appears anywhere in the person's name.

        Returns:
            Optional[List[str]]: List of xref_ids for matching people, or None if no matches found.
        """
        matches = []
        search_name = name.lower().strip()
        
        for person_id, person in self.people.items():
            if person.name:
                person_name = person.name.lower()
                if exact_match:
                    if person_name == search_name:
                        matches.append(person_id)
                else:
                    if search_name in person_name:
                        matches.append(person_id)
        
        if matches:
            logger.info(f"Found {len(matches)} person(s) matching '{name}': {matches}")
            return matches
        else:
            logger.warning(f"No person found with name '{name}'")
            return None
        
    def export_people_with_photos(self, people: Dict[str, 'Person'], new_gedcom_path: Path, photo_dir: Path) -> None:
        """
        Export all people to a new GEDCOM file, copying any referenced photo images to a new directory.

        Args:
            people (Dict[str, Person]): Dictionary of Person objects to export.
            new_gedcom_path (Path): Path to write the new GEDCOM file.
            photo_dir (Path): Directory to copy photo images into.
        """
        # Write GEDCOM file with updated photo paths
        self.gedcom_parser.gedcom_writer(people, new_gedcom_path, photo_dir)