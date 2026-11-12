"""Тесты разбора аргументов команды /add (bot/handlers.py, parse_add_args)."""

from datetime import date

from bot.handlers import parse_add_args


def test_name_and_date():
    assert parse_add_args("Йогурт; 12.05.2027") == ("Йогурт", date(2027, 5, 12))


def test_name_only_without_date():
    assert parse_add_args("Соль") == ("Соль", None)


def test_semicolon_without_date():
    assert parse_add_args("Соль;") == ("Соль", None)


def test_empty_name_is_rejected():
    assert parse_add_args("; 01.01.2027") is None
    assert parse_add_args("") is None


def test_bad_date_is_rejected():
    assert parse_add_args("Кефир; 32.13.2027") is None
    assert parse_add_args("Кефир; 2027-05-12") is None


def test_long_name_is_rejected():
    assert parse_add_args("x" * 101) is None
