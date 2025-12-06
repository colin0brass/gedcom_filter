import pytest
from geo_gedcom.gedcom_date import GedcomDate
from ged4py.calendar import GregorianDate

def test_simple_year():
    gd = GedcomDate("1900")
    result = gd.resolved
    assert isinstance(result, GregorianDate)
    assert result.year == 1900

def test_month_year():
    gd = GedcomDate("JUL 1913")
    result = gd.resolved
    assert isinstance(result, GregorianDate)
    assert result.year == 1913
    assert result.month == 'JUL'

def test_full_date():
    gd = GedcomDate("15 JUL 1913")
    result = gd.resolved
    assert isinstance(result, GregorianDate)
    assert result.year == 1913
    assert result.month == 'JUL'
    assert result.day == 15

def test_range():
    gd = GedcomDate("BET JUL AND SEP 1913", simplify_range_policy='none')
    result = gd.resolved
    assert isinstance(result, tuple)
    assert result[0].month == 'JUL'
    assert result[1].month == 'SEP'
    assert result[0].year == 1913
    assert result[1].year == 1913

def test_ordinal_date():
    gd = GedcomDate("21st July 1913")
    result = gd.resolved
    assert isinstance(result, GregorianDate)
    assert result.day == 21
    assert result.month == 'JUL'
    assert result.year == 1913

def test_fallback_phrase():
    gd = GedcomDate("Spring 1913")
    result = gd.resolved
    assert isinstance(result, GregorianDate) or isinstance(result, str)

def test_abt_year():
    gd = GedcomDate("ABT 1762")
    result = gd.resolved
    assert isinstance(result, GregorianDate) or isinstance(result, str)
    if isinstance(result, GregorianDate):
        assert result.year == 1762
    else:
        assert result.startswith("ABT")

def test_bet_year_range():
    gd = GedcomDate("BET 1914 AND 1920", simplify_range_policy='none')
    result = gd.resolved
    assert isinstance(result, tuple)
    assert result[0].year == 1914
    assert result[1].year == 1920

def test_bef_year():
    gd = GedcomDate("BEF 1951")
    result = gd.resolved
    assert isinstance(result, GregorianDate) or isinstance(result, str)
    if isinstance(result, GregorianDate):
        assert result.year == 1951
    else:
        assert result.startswith("BEF")

def test_bet_month_range():
    gd = GedcomDate("BET JAN AND MAR 1894", simplify_range_policy='none')
    result = gd.resolved
    assert isinstance(result, tuple)
    assert result[0].month == 'JAN'
    assert result[1].month == 'MAR'
    assert result[0].year == 1894
    assert result[1].year == 1894

def test_simple_day_month_year():
    gd = GedcomDate("4 DEC 2025")
    result = gd.resolved
    assert isinstance(result, GregorianDate)
    assert result.year == 2025
    assert result.month == 'DEC'
    assert result.day == 4

def test_simple_year_only():
    gd = GedcomDate("1759")
    result = gd.resolved
    assert isinstance(result, GregorianDate)
    assert result.year == 1759

def test_month_year_with_space():
    gd = GedcomDate("AUG 1812")
    result = gd.resolved
    assert isinstance(result, GregorianDate)
    assert result.year == 1812
    assert result.month == 'AUG'

def test_abt_year_phrase():
    gd = GedcomDate("abt 1776")
    result = gd.resolved
    assert isinstance(result, GregorianDate) or isinstance(result, str)
    if isinstance(result, GregorianDate):
        assert result.year == 1776
    else:
        assert result.lower().startswith("abt")

def test_bef_year_phrase():
    gd = GedcomDate("bef 1832")
    result = gd.resolved
    assert isinstance(result, GregorianDate) or isinstance(result, str)
    if isinstance(result, GregorianDate):
        assert result.year == 1832
    else:
        assert result.lower().startswith("bef")

def test_bet_years():
    gd = GedcomDate("BET 1801 AND 1836", simplify_range_policy='none')
    result = gd.resolved
    assert isinstance(result, tuple)
    assert result[0].year == 1801
    assert result[1].year == 1836

def test_bet_months():
    gd = GedcomDate("BET NOV AND DEC 1831", simplify_range_policy='none')
    result = gd.resolved
    assert isinstance(result, tuple)
    assert result[0].month == 'NOV'
    assert result[1].month == 'DEC'
    assert result[0].year == 1831
    assert result[1].year == 1831

def test_year_with_text():
    gd = GedcomDate("Estimated Birth Year: abt 1776")
    result = gd.resolved
    assert isinstance(result, GregorianDate) or isinstance(result, str)
    if isinstance(result, GregorianDate):
        assert result.year == 1776
    else:
        assert "1776" in result

def test_year_with_season():
    gd = GedcomDate("Winter 1894")
    result = gd.resolved
    assert isinstance(result, GregorianDate) or isinstance(result, str)
    if isinstance(result, GregorianDate):
        assert result.year == 1894
    else:
        assert "Winter" in result

# Add more edge cases as needed
