"""Тесты выборки и форматирования продуктов."""

from datetime import date, datetime

import pytest

from bot.formatting import format_products
from core.notifications import TZ
from core.products import list_user_products
from core.users import get_or_create_user
from models import Product


@pytest.mark.asyncio
async def test_list_products_sorted_by_expiry_and_none_last(session):
    user = await get_or_create_user(session, 777)
    session.add_all(
        [
            Product(user_id=user.id, name="Молоко", expiry_date=date(2026, 12, 1)),
            Product(user_id=user.id, name="Соль", expiry_date=None),
            Product(user_id=user.id, name="Кефир", expiry_date=date(2026, 11, 20)),
        ]
    )
    await session.commit()

    names = [p.name for p in await list_user_products(session, user.id)]
    assert names == ["Кефир", "Молоко", "Соль"]


@pytest.mark.asyncio
async def test_list_products_only_for_given_user(session):
    alice = await get_or_create_user(session, 1)
    bob = await get_or_create_user(session, 2)
    session.add(Product(user_id=bob.id, name="Чужой", expiry_date=date(2026, 12, 1)))
    await session.commit()

    assert await list_user_products(session, alice.id) == []


def test_format_products_empty():
    assert "нет продуктов" in format_products([])


def test_format_products_shows_name_date_and_escapes_html():
    items = [
        Product(name="<b>Йогурт</b>", expiry_date=date(2026, 11, 20)),
        Product(name="Соль", expiry_date=None),
    ]
    now = datetime(2026, 11, 13, 10, 0, tzinfo=TZ)
    text = format_products(items, now)

    assert "• &lt;b&gt;Йогурт&lt;/b&gt; — до 20.11.2026, осталось 7 дней" in text
    assert "• Соль — срок не указан" in text


def test_format_products_hours_under_24h_and_days_otherwise():
    items = [
        # дедлайн 14.11 00:00; сейчас 13.11 10:00 → 14 часов
        Product(name="Молоко", expiry_date=date(2026, 11, 13)),
        # дедлайн 14.11 00:00; сейчас 13.11 23:30 → 30 минут, показываем 1 ч
        Product(name="Кефир", expiry_date=date(2026, 11, 13)),
        # дедлайн 15.11 00:00; сейчас 13.11 10:00 → больше суток → дни
        Product(name="Сыр", expiry_date=date(2026, 11, 14)),
        # дедлайн 13.11 00:00 уже прошёл
        Product(name="Хлеб", expiry_date=date(2026, 11, 12)),
    ]
    text = format_products(items, datetime(2026, 11, 13, 10, 0, tzinfo=TZ))
    assert "• Молоко — до 13.11.2026, осталось 14 ч" in text
    assert "• Сыр — до 14.11.2026, осталось 1 день" in text
    assert "• Хлеб — до 12.11.2026, срок истёк 1 день назад" in text

    text = format_products(items[:2], datetime(2026, 11, 13, 23, 30, tzinfo=TZ))
    assert "осталось 1 ч" in text
