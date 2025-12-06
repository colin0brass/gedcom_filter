"""
Partner.py - Partner class for GEDCOM mapping.

Defines:
    - Partner: Represents a partner relationship for a person.

Author: @colin0brass
Last updated: 2025-12-06
"""

from .lat_lon import LatLon

class Partner:
    """
    Represents a partner relationship for a person (not widely used in main logic).

    Attributes:
        xref_id (str): Partner's GEDCOM cross-reference ID.
        latlon (Optional[LatLon]): Latitude/longitude of the partner.
    """
    __slots__ = ['xref_id', 'latlon']
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
