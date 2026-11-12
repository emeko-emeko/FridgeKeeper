"""Выборки для команд /soon и /delete."""

from datetime import date

import pytest

from core.products import find_products_by_name, products_expiring_within
from core.users import get_or_create_user
from models import Product


@pytest.mark.asyncio
async def test_expiring_within_includes_expired_and_excludes_far(session):
    user = await get_or_create_user(session, 901)
    today = date(2026, 11, 13)
    session.add_all([
        Product(user_id=user.id, name="Просрочен", expiry_date=date(2026, 11, 10)),
        Product(user_id=user.id, name="Завтра", expiry_date=date(2026, 11, 14)),
        Product(user_id=user.id, name="Через месяц", expiry_date=date(2026, 12, 13)),
        Product(user_id=user.id, name="Без срока", expiry_date=None),
    ])
    await session.commit()

    rows = await products_expiring_within(session, user.id, today, days=3)

    assert [p.name for p in rows] == ["Просрочен", "Завтра"]


@pytest.mark.asyncio
async def test_find_by_name_ignores_case_and_spaces_and_other_users(session):
    user = await get_or_create_user(session, 902)
    other = await get_or_create_user(session, 903)
    session.add_all([
        Product(user_id=user.id, name="Йогурт"),
        Product(user_id=other.id, name="Йогурт"),
    ])
    await session.commit()

    rows = await find_products_by_name(session, user.id, "  йогурт ")

    assert len(rows) == 1
    assert rows[0].user_id == user.id


def test_bot_menu_commands_are_all_in_help():
    from bot.formatting import BOT_COMMANDS, HELP_TEXT

    for command, description in BOT_COMMANDS:
        assert f"/{command}" in HELP_TEXT
        assert 0 < len(description) <= 256
