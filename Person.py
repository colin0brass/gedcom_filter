"""
Person.py - Person and LifeEvent classes for GEDCOM mapping.

Defines:
    - Person: Represents an individual in the GEDCOM file, with attributes for names, events, relationships, and photos.
    - LifeEvent: Represents a life event (birth, death, marriage, etc.) for a person, including date and place.

Authors: @lmallez, @D-jeffrey, @colin0brass
Last updated: 2025-11-29
"""

__all__ = ['Person', 'LifeEvent']

import logging
import re
from typing import Dict, Union, Optional, List

from LatLon import LatLon
from location import Location
from ged4py.model import Record, NameRec

logger = logging.getLogger(__name__)

class Partner:
    """
    Represents a partner relationship for a person (not widely used in main logic).

    Attributes:
        xref_id (str): Partner's GEDCOM cross-reference ID.
        latlon (Optional[LatLon]): Latitude/longitude of the partner.
    """
    def __init__(self, xref_id, latlon : LatLon = None):
        """
        Initialize a Partner.

        Args:
            xref_id (str): Partner's GEDCOM cross-reference ID.
            latlon (Optional[LatLon]): Latitude/longitude of the partner.
        """
        self.xref_id = xref_id
        self.latlon :LatLon = latlon

    def __str__(self):
        return f"Person(id={self.xref_id}, LatLon={self.latlon})"

    def __repr__(self) -> str:
        return f'[ {self.xref_id} : LatLon={self.latlon} ]'
 
class Person:
    """
    Represents a person in the GEDCOM file.

    Attributes:
        xref_id (str): GEDCOM cross-reference ID.
        name (Optional[str]): Full name.
        father (Optional[Person]): Father (xref ID or Person).
        mother (Optional[Person]): Mother (xref ID or Person).
        latlon (Optional[LatLon]): Latitude/longitude (best known position).
        birth (Optional[LifeEvent]): Birth event.
        death (Optional[LifeEvent]): Death event.
        marriages (List[LifeEvent]): Marriage events.
        residences (List[LifeEvent]): Residence events.
        firstname (Optional[str]): First name.
        surname (Optional[str]): Surname.
        maidenname (Optional[str]): Maiden name.
        sex (Optional[str]): Sex.
        title (Optional[str]): Title.
        children (List[str]): List of children xref IDs.
        partners (List[str]): List of partner xref IDs.
        age (Any): Age or age with cause of death.
        photos_all (List[str]): All photo file paths or URLs.
        photo (Optional[str]): Primary photo file path or URL.
        location (Any): Best known location.
        family_spouse (List[str]): FAMS family IDs (as spouse/partner).
        family_child (List[str]): FAMC family IDs (as child).
    """
    __slots__ = ['xref_id', 'name', 'father', 'mother', 'latlon', 'birth', 'death', 'marriages', 'residences', 'firstname', 
                 'surname', 'maidenname','sex','title', 'photos_all', 'photo', 'children', 'partners', 'age', 'location',
                 'family_spouse', 'family_child']
    def __init__(self, xref_id : str):
        """
        Initialize a Person instance with all relationship, event, and metadata fields.

        Args:
            xref_id (str): GEDCOM cross-reference ID.
        """
        self.xref_id = xref_id
        self.name : Optional[str] = None
        self.father : Person = None
        self.mother : Person = None
        self.latlon : LatLon = None           # save the best postion
        self.birth : LifeEvent = None
        self.death : LifeEvent = None
        self.marriages : List[LifeEvent] = []
        self.residences : List[LifeEvent] = []
        self.firstname : Optional[str] = None               # firstname Name
        self.surname : Optional[str] = None             # Last Name
        self.maidenname : Optional[str] = None
        self.sex : Optional[str] = None
        self.title : Optional[str] = None
        self.children : List[str] = []
        self.partners : List[str] = []
        self.age = None           # This can be age number or a including the cause of death
        self.photos_all = []         # URL or file path to photos
        self.photo : Optional[str] = None        # URL or file path to primary photo
        self.location = None
        self.family_spouse = []
        self.family_child = []

    def __str__(self) -> str:
        """
        Returns a string representation of the person (xref and name).
        """
        return f"Person(id={self.xref_id}, name={self.name})"

    def __repr__(self) -> str:
        """
        Returns a detailed string representation of the person for debugging.
        """
        return f"[ {self.xref_id} : {self.name} - {self.father} & {self.mother} - {self.latlon} ]"

    # return "year (Born)" or "year (Died)" or "? (Unknown)" along with year as a string or None
    # Example "2010 (Born)", "2010" or "1150 (Died)", "1150" or "? (Unknown)"
    def refyear(self):
        """
        Returns a tuple of (best year string, year) for the person, based on birth or death.
        """
        bestyear = "? (Unknown)"
        year = None
        if self.birth and self.birth.date:
            year = self.birth.whenyear()
            bestyear = f"{self.birth.whenyear()} (Born)" if year else bestyear
        elif self.death and self.death.date:
            year = self.death.whenyear()
            bestyear = f"{self.death.whenyear()} (Died)" if year else bestyear
        return (bestyear, year)

    def ref_year(self) -> str:
        """
        Returns a reference year string for the person.

        Returns:
            str: Reference year string.
        """
        if self.birth and self.birth.date:
            return f'Born {self.birth.date_year()}'
        if self.death and self.death.date:
            return f'Died {self.death.date_year()}'
        return 'Unknown'
    
    def bestlocation(self):
        """
        Returns the best known location for the person as [latlon, description].
        """
        best = ["Unknown", ""]
        if self.birth and self.birth.location:
            best = [
                str(self.birth.location.latlon),
                f"{self.birth.place} (Born)" if self.birth.place else "",
            ]
        elif self.death and self.death.location:
            best = [
                str(self.death.location.latlon),
                f"{self.death.place} (Died)" if self.death.place else "",
            ]
        return best

    def bestLatLon(self):
        """
        Returns the best known LatLon for the person (birth, then death, else None).
        """
        best = LatLon(None, None)
        if self.birth and self.birth.latlon and self.birth.latlon.hasLocation():
            best = self.birth.latlon
        elif self.death and self.death.latlon and self.death.latlon.hasLocation():
            best = self.death.latlon
        return best
    
class LifeEvent:
    """
    Represents a life event (birth, death, marriage, etc.) for a person.

    Attributes:
        place (Optional[str]): The place where the event occurred.
        date: The date of the event (string or ged4py date object).
        what (Optional[str]): The type of event (e.g., 'BIRT', 'DEAT').
        record (Optional[Record]): The GEDCOM record associated with the event.
        location (Optional[Location]): Geocoded location object.
    """
    __slots__ = [
        'place',
        'date',
        'what',
        'record',
        'location'
        
    ]
    def __init__(self, place: str, atime, position: Optional[LatLon] = None, what=None, record: Optional[Record] = None):
        """
        Initialize a LifeEvent instance.

        Args:
            place (str): Place of the event.
            atime: Date of the event (string or ged4py date object).
            position (Optional[LatLon]): Latitude/longitude.
            what (Optional[str]): Type of event (e.g., 'BIRT', 'DEAT').
            record (Optional[Record]): GEDCOM record.
        """
        self.place: Optional[str] = place
        self.date = atime
        self.what: Optional[str] = what
        self.record = record
        self.location: Location = Location(position=position, address=place) if position or place else None
        

    def __repr__(self) -> str:
        """
        Returns a string representation of the LifeEvent for debugging.
        """
        if self.what:
            return f"[ {self.date} : {self.place} is {self.what}]"
        return f'[ {self.date} : {self.place} ]'
    
    def asEventstr(self):
        """
        Returns a string describing the event (date and place).
        """
        if self:
            place = f" at {self.getattr('place')}" if self.place is not None else ""
            date = f" on {self.getattr('date')}" if self.date else ""
            return f"{date}{place}"
        return ""
    
    def DateFromField(field):
        if field:
            if not isinstance(field, str):
                field = str(field)
            # BC or B.C
            if field.lower().find("bc") > 0 or field.lower().find("b.c") > 0:
                    return -int(field[:field.lower().find("b")])
            if len(field) > 3 and field[3].isdigit():
                try:
                    return int(field[:4])
                except:
                    pass
            try:
                return int(field)
            except:
                digits = ''
                for char in field:
                    if char.isdigit() or char == '-':
                        digits += char
                return int(digits) if digits else None
        return None


    def whenyear(self, last = False) -> Optional[str]:
        """
        Returns the year (as string) for the event date, if available.

        Args:
            last (bool): If True, returns the last year in a range.

        Returns:
            Optional[str]: Year string or None.
        """
        if self.date:
            if isinstance(self.date, str):
                return (self.date)
            else:
                if self.date.value.kind.name == "RANGE" or self.date.value.kind.name == "PERIOD":
                    if last:
                        return self.date.value.date1.year_str
                    else:
                        return self.date.value.date2.year_str
                elif self.date.value.kind.name == "PHRASE":
                    # use match.group(0) to extract the year safely
                    m = re.search(r"-?\d{3,4}", self.date.value.phrase)
                    if m:
                        return m.group(0)
                    return None
                else:
                    return self.date.value.date.year_str
        return None

    def whenyearnum(self, last = False):
        """
        Returns the year as an integer (or 0 if not available).
        """
        from Person import DateFromField
        return DateFromField(self.whenyear(last))

    def getattr(self, attr):
        """
        Returns the value of a named attribute for the event, with some aliases.
        """
        if attr == 'latlon':
            return self.location.latlon if self.location else None
        elif attr == 'when' or attr == 'date':
            return getattr(self.date, 'value', "")
        elif attr == 'where' or attr == 'place':
            return self.place if self.place else None
        elif attr == 'what':
            return self.what if self.what else ""
        logger.warning("LifeEvent attr: %s' object has no attribute '%s'", type(self).__name__, attr)    
        return None

    def __str__(self) -> str:
        """
        Returns a string summary of the event (place, date, latlon, what).
        """
        return f"{self.getattr('place')} : {self.getattr('date')} - {self.getattr('latlon')} {self.getattr('what')}"
    
    def date_year(self, last: bool = False) -> Optional[str]:
        """
        Returns the year string for the event date.

        Args:
            last (bool): If True, returns the last year in a range.

        Returns:
            Optional[str]: Year string or None.
        """
        if self.date:
            if isinstance(self.date, str):
                return self.date
            else:
                kind = getattr(self.date.value, 'kind', None)
                if kind and kind.name in ('RANGE', 'PERIOD'):
                    if last:
                        return self.date.value.date1.year_str
                    else:
                        return self.date.value.date2.year_str
                elif kind and kind.name == 'PHRASE':
                    # Safely extract a 3- or 4-digit year (allow optional leading minus)
                    phrase = getattr(getattr(self.date, 'value', None), 'phrase', None)
                    if not phrase:
                        logger.warning('LifeEvent: date_year: no phrase available on date.value')
                        return None
                    m = re.search(r'-?\d{3,4}', phrase)
                    if m:
                        return m.group(0)
                    logger.warning('LifeEvent: date_year: unable to parse date phrase: %s', phrase)
                    return None
                else:
                    return getattr(self.date.value.date, 'year_str', None)
        return None

    def __getattr__(self, name):
        if name == 'pos':
            return (None, None)
        return None