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


def normalize_first_name(first_name: str | None) -> str | None:
    """Имя из Telegram: без пробелов по краям, не длиннее 64 символов. Пустое или None — None."""
    if not first_name:
        return None
    name = first_name.strip()[:64]
    return name or None


async def get_or_create_user(
    session: AsyncSession, telegram_id: int, first_name: str | None = None
) -> User:
    """Возвращает пользователя с данным telegram_id, создавая его при отсутствии.

    Если передано first_name и оно отличается от сохранённого, обновляет его.
    Пустое first_name ничего не меняет.
    """
    name = normalize_first_name(first_name)
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(telegram_id=telegram_id, first_name=name)
        session.add(user)
        await session.commit()
    elif name is not None and user.first_name != name:
        user.first_name = name
        await session.commit()
    return user


async def mark_bot_started(
    session: AsyncSession, telegram_id: int, first_name: str | None = None
) -> User:
    """Фиксирует, что пользователь открыл бота (/start или подтверждение входа).

    Пишет bot_started_at только если поле пустое: повторные вызовы ничего не меняют.
    """
    user = await get_or_create_user(session, telegram_id, first_name)
    if user.bot_started_at is None:
        user.bot_started_at = datetime.now(UTC)  # aware: PostgreSQL хранит timestamptz
        await session.commit()
    return user
