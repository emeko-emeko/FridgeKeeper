# tests/test_expiry_parser.py
from datetime import date

from core.expiry_parser import parse_expiry


def test_numeric_after_marker():
    assert parse_expiry("Годен до 12.05.2027") == date(2027, 5, 12)


def test_two_digit_year_and_slashes():
    assert parse_expiry("Срок годности: 03/11/26") == date(2026, 11, 3)


def test_textual_month():
    assert parse_expiry("Использовать до 5 марта 2027 г.") == date(2027, 3, 5)


def test_skips_production_date():
    text = "Дата производства: 01.05.2027. Годен до 20.05.2027"
    assert parse_expiry(text) == date(2027, 5, 20)


def test_no_marker_returns_none():
    assert parse_expiry("Молоко 2.5%, 1 л") is None