"""Работа с пользователями: получение или создание записи по Telegram ID."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User


async def create_web_user(session: AsyncSession) -> User:
    """Создаёт аккаунт сайта без Telegram. Привязать Telegram можно токеном связки."""
    user = User(telegram_id=None)
    session.add(user)
    await session.commit()
    return user


async def get_or_create_user(session: AsyncSession, telegram_id: int) -> User:
    """Возвращает пользователя с данным telegram_id, создавая его при отсутствии."""
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.commit()
    return user


async def mark_bot_started(session: AsyncSession, telegram_id: int) -> User:
    """Фиксирует, что пользователь открыл бота (/start или подтверждение входа).

    Пишет bot_started_at только если поле пустое: повторные вызовы ничего не меняют.
    """
    user = await get_or_create_user(session, telegram_id)
    if user.bot_started_at is None:
        user.bot_started_at = datetime.now(UTC)  # aware: PostgreSQL хранит timestamptz
        await session.commit()
    return user
