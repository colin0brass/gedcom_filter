def test_imports():
    from gedcom import Gedcom, GedcomParser, Person, LifeEvent, Location, LatLon, FuzzyAddressBook, GedcomDate
    assert Gedcom
    assert GedcomParser
    assert Person
    assert LifeEvent
    assert Location
    assert LatLon
    assert FuzzyAddressBook
    assert GedcomDate
