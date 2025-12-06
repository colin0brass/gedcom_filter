import pytest
from geo_gedcom import LifeEvent, Location, LatLon

def test_life_event_init():
    event = LifeEvent(place="London", date="1900", position=LatLon(51.5, -0.1), what="BIRT")
    assert event.place == "London"
    assert event.date is not None
    assert event.location is not None
    assert event.what == "BIRT"

def test_life_event_birth_full_date_place():
    event = LifeEvent(place="Luanshya, Zambia", date="16 JUN 1970", what="BIRT")
    assert event.place == "Luanshya, Zambia"
    assert event.date.year_num == 1970
    assert event.date.single.month == "JUN"
    assert event.what == "BIRT"

def test_life_event_birth_year_only():
    event = LifeEvent(place=None, date="1759", what="BIRT")
    assert event.date.year_num == 1759
    assert event.place is None

def test_life_event_birth_about():
    event = LifeEvent(place=None, date="ABT 1762", what="BIRT")
    assert event.date.year_num == 1762
    assert event.place is None

def test_life_event_residence_year_place():
    event = LifeEvent(place="Eastfield, Hickling, Norfolk, England", date="1841", what="RESI")
    assert event.place == "Eastfield, Hickling, Norfolk, England"
    assert event.date.year_num == 1841
    assert event.what == "RESI"

def test_life_event_baptism_full_date_place():
    event = LifeEvent(place="Norfolk, England", date="13 NOV 1831", what="BAPM")
    assert event.place == "Norfolk, England"
    assert event.date.year_num == 1831
    assert event.date.single.month == "NOV"
    assert event.what == "BAPM"

def test_life_event_death_full_date_place():
    event = LifeEvent(place="Swansea, Glamorgan, Wales", date="24 NOV 1990", what="DEAT")
    assert event.place == "Swansea, Glamorgan, Wales"
    assert event.date.year_num == 1990
    assert event.date.single.month == "NOV"
    assert event.what == "DEAT"

def test_life_event_burial_year_place():
    event = LifeEvent(place="North Mymms, Welwyn Hatfield District, Hertfordshire, England", date="1812", what="BURI")
    assert event.place == "North Mymms, Welwyn Hatfield District, Hertfordshire, England"
    assert event.date.year_num == 1812
    assert event.what == "BURI"
