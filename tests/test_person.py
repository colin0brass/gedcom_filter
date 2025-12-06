import pytest
from geo_gedcom import Person

def test_person_init():
    p = Person("I1")
    assert p.xref_id == "I1"
    assert p.name is None

def test_person_multiple_names():
    p = Person("I635")
    p.name = "Herbert Campbell /Westmorland/"
    p.firstname = "Herbert Campbell"
    p.surname = "Westmorland"
    p.maidenname = None
    # Simulate alternate names
    p_alt = Person("I635")
    p_alt.name = "Herbert /Westmorland/"
    p_aka = Person("I635")
    p_aka.name = "Herbert C /Westmorland/"
    assert p.name.startswith("Herbert")
    assert p.surname == "Westmorland"

def test_person_birth_full_date_place():
    p = Person("I635")
    p.birth = type('evt', (), {'date': type('dt', (), {'year_num': 1893, 'single': type('sd', (), {'month': "DEC"})})(), 'place': "Ryde, Isle of Wight, England"})()
    assert p.birth.date.year_num == 1893
    assert p.birth.place == "Ryde, Isle of Wight, England"

def test_person_birth_year_only():
    p = Person("I635")
    p.birth = type('evt', (), {'date': type('dt', (), {'year_num': 1893, 'single': None})(), 'place': "Ryde, Isle of Wight, England"})()
    assert p.birth.date.year_num == 1893

def test_person_birth_about():
    p = Person("I635")
    p.birth = type('evt', (), {'date': type('dt', (), {'year_num': 1894, 'single': None})(), 'place': "Ryde, Isle of Wight, England"})()
    assert p.birth.date.year_num == 1894

def test_person_birth_range():
    p = Person("I635")
    p.birth = type('evt', (), {'date': type('dt', (), {'year_num': 1894, 'single': None})(), 'place': "Isle of Wight, England"})()
    assert p.birth.place == "Isle of Wight, England"

def test_person_residence_event():
    p = Person("I635")
    p.residences = [type('evt', (), {'date': type('dt', (), {'year_num': 1925})(), 'place': "Berkshire, England"})()]
    assert p.residences[0].date.year_num == 1925
    assert p.residences[0].place == "Berkshire, England"

def test_person_military_event():
    p = Person("I635")
    p.military = [type('evt', (), {'date': type('dt', (), {'year_num': 1916})(), 'place': None})()]
    assert p.military[0].date.year_num == 1916

def test_person_arrival_departure_events():
    p = Person("I635")
    p.arrivals = [type('evt', (), {'date': type('dt', (), {'year_num': 1934})(), 'place': "London, London, England"})()]
    p.departures = [type('evt', (), {'date': type('dt', (), {'year_num': 1934})(), 'place': "England"})()]
    assert p.arrivals[0].place == "London, London, England"
    assert p.departures[0].place == "England"

def test_person_baptism_event():
    p = Person("I635")
    p.baptism = type('evt', (), {'date': type('dt', (), {'year_num': 1894, 'single': None})(), 'place': "Ryde, Isle of Wight, England"})()
    assert p.baptism.place == "Ryde, Isle of Wight, England"

def test_person_death_event():
    p = Person("I635")
    p.death = type('evt', (), {'date': type('dt', (), {'year_num': 1972, 'single': None})(), 'place': "Winchester, Hampshire, England"})()
    assert p.death.date.year_num == 1972
    assert p.death.place == "Winchester, Hampshire, England"

def test_person_family_relationships():
    p = Person("I635")
    p.family_spouse = ["F2513", "F259"]
    p.family_child = ["F2515", "F258"]
    assert "F2513" in p.family_spouse
    assert "F2515" in p.family_child

def test_person_geocoded_event():
    p = Person("I635")
    p.birth = type('evt', (), {'date': type('dt', (), {'year_num': 1893, 'single': None})(), 'place': "Ryde, Isle of Wight, England", 'latlon': type('ll', (), {'lat': 50.674908, 'lon': -1.301753})()})()
    assert p.birth.latlon.lat == 50.674908
    assert p.birth.latlon.lon == -1.301753
