"""Работа с продуктами пользователя."""

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
