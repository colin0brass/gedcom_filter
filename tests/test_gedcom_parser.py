import pytest
from geo_gedcom.gedcom_parser import GedcomParser
from pathlib import Path

def test_gedcom_parser_init():
    parser = GedcomParser(gedcom_file=None)
    assert parser.gedcom_file is None or isinstance(parser.gedcom_file, Path)
