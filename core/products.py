"""Работа с продуктами пользователя."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Product


async def list_user_products(session: AsyncSession, user_id: int) -> list[Product]:
    """Продукты пользователя, отсортированные по сроку годности.

    Продукты без срока годности выводятся в конце списка.
    """
    result = await session.scalars(
        select(Product)
        .where(Product.user_id == user_id)
        .order_by(Product.expiry_date.is_(None), Product.expiry_date, Product.id)
    )
    return list(result)


async def products_expiring_within(
    session: AsyncSession, user_id: int, today: date, days: int
) -> list[Product]:
    """Продукты, у которых срок истекает в ближайшие `days` дней, включая уже просроченные."""
    result = await session.scalars(
        select(Product)
        .where(
            Product.user_id == user_id,
            Product.expiry_date.is_not(None),
            Product.expiry_date <= today + timedelta(days=days),
        )
        .order_by(Product.expiry_date, Product.id)
    )
    return list(result)


async def find_products_by_name(session: AsyncSession, user_id: int, name: str) -> list[Product]:
    """Продукты пользователя с совпадающим названием (без учёта регистра и пробелов по краям)."""
    wanted = name.strip().casefold()
    products = await session.scalars(select(Product).where(Product.user_id == user_id))
    return [p for p in products if p.name.strip().casefold() == wanted]
