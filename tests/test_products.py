"""Тесты выборки и форматирования продуктов."""

from datetime import date

import pytest

from bot.formatting import format_products
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
    text = format_products(items)

    assert "• &lt;b&gt;Йогурт&lt;/b&gt; — до 20.11.2026" in text
    assert "• Соль — до срок не указан" in text
