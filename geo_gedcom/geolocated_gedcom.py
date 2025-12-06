from geo_gedcom.gedcom import Gedcom
from .location import Location
from .addressbook import FuzzyAddressBook
from pathlib import Path

class GeolocatedGedcom(Gedcom):
    """
    Extends Gedcom to add geolocation features.
    
    Attributes:
        address_book (FuzzyAddressBook): Address book for geocoding locations.
    """
    __slots__ = ['address_book']
    logger_interval = 20

    def __init__(
            self,
            gedcom_file: Path,
            only_use_photo_tags: bool = False
            ):
        super().__init__(gedcom_file, only_use_photo_tags)
        self.address_book = FuzzyAddressBook()
        self._geocode_locations()

    def _geocode_locations(self):
        """
        Geocode all unique locations in the GEDCOM using the address book.
        """
        unique_locations = {event.place for person in self.people.values() for event in person.life_events if event.place}
        for loc in unique_locations:
            location = Location(place_name=loc)
            self.address_book.geocode_location(location)