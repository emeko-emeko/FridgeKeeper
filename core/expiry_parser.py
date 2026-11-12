"""Поиск срока годности в тексте, который вернул OCR. Только регулярные выражения."""

import re
from datetime import date

# Маркеры, после которых обычно стоит дата окончания срока
MARKERS = (
    "годен до",
    "годен:",
    "срок годности",
    "использовать до",
    "употребить до",
    "годно до",
)

# Даты, стоящие сразу после этих слов, относятся к производству, а не к сроку
EXCLUDE_BEFORE = ("производ", "изготов", "фасов", "выработ")

MONTH_PREFIXES = (
    ("янв", 1), ("фев", 2), ("мар", 3), ("апр", 4), ("мая", 5), ("май", 5),
    ("июн", 6), ("июл", 7), ("авг", 8), ("сен", 9), ("окт", 10), ("ноя", 11), ("дек", 12),
)

NUMERIC_RE = re.compile(r"(?<!\d)(\d{2})[./-](\d{2})[./-](\d{4}|\d{2})(?!\d)")
TEXTUAL_RE = re.compile(r"(?<!\d)(\d{1,2})\s+([а-яё]+)\s+(\d{4})(?!\d)")
WINDOW = 40  # символов после маркера, в которых ищем дату


def _month_number(word: str) -> int | None:
    for prefix, number in MONTH_PREFIXES:
        if word.startswith(prefix):
            return number
    return None


def _to_date(day: int, month: int, year: int) -> date | None:
    if year < 100:
        year += 2000
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _find_dates(fragment: str) -> list[tuple[int, date]]:
    """Все корректные даты во фрагменте вместе с позицией."""
    found: list[tuple[int, date]] = []
    for m in NUMERIC_RE.finditer(fragment):
        d = _to_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if d:
            found.append((m.start(), d))
    for m in TEXTUAL_RE.finditer(fragment):
        month = _month_number(m.group(2))
        if month:
            d = _to_date(int(m.group(1)), month, int(m.group(3)))
            if d:
                found.append((m.start(), d))
    return sorted(found, key=lambda item: item[0])


def parse_expiry(text: str) -> date | None:
    """Возвращает дату окончания срока или None, если её не нашли (тогда просим ввести вручную)."""
    lowered = text.lower()
    for marker in MARKERS:
        start = 0
        while (pos := lowered.find(marker, start)) != -1:
            start = pos + len(marker)
            window = lowered[start:start + WINDOW]
            for offset, found in _find_dates(window):
                before = window[:offset]
                if any(word in before for word in EXCLUDE_BEFORE):
                    continue
                return found
    return None


def parse_expiry_guess(text: str) -> date | None:
    """Запасной вариант, когда маркера нет: самая поздняя дата на этикетке.

    Производство обычно раньше срока, поэтому поздняя дата чаще всего и есть срок.
    Результат — предположение: показывать пользователю только с подтверждением.
    """
    dates = [d for _, d in _find_dates(text.lower())]
    return max(dates) if dates else None
