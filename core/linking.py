"""Связывание веб-аккаунта с Telegram через одноразовый токен.

Поток:
1. Сайт вызывает create_link_token(user_id) и показывает ссылку build_link_url(...).
2. Пользователь переходит по ссылке, бот получает /start <token>.
3. Бот вызывает consume_link_token(...), который проверяет токен и записывает telegram_id.
"""

import hashlib
import secrets
from datetime import timedelta
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import LINK_TOKEN_TTL_MINUTES
from models import LinkToken, User, utcnow


class LinkStatus(Enum):
    """Результат попытки погасить токен связки."""

    OK = "ok"                        # аккаунты связаны
    INVALID = "invalid"              # токен не найден
    EXPIRED = "expired"              # срок действия истёк
    USED = "used"                    # токен уже использован
    ALREADY_LINKED = "already_linked"  # аккаунт сайта или Telegram уже связан с другим


def _hash_token(raw_token: str) -> str:
    """Хэш токена для хранения в БД (сам токен в БД не сохраняется)."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def create_link_token(
    session: AsyncSession,
    user_id: int,
    ttl_minutes: int = LINK_TOKEN_TTL_MINUTES,
) -> str:
    """Создаёт одноразовый токен и возвращает его открытое значение.

    Открытый токен возвращается только один раз, в БД хранится хэш.
    """
    raw_token = secrets.token_urlsafe(32)  # 43 символа из допустимого набора для deep link
    session.add(
        LinkToken(
            token_hash=_hash_token(raw_token),
            user_id=user_id,
            expires_at=utcnow() + timedelta(minutes=ttl_minutes),
        )
    )
    await session.commit()
    return raw_token


async def consume_link_token(
    session: AsyncSession,
    raw_token: str,
    telegram_id: int,
) -> LinkStatus:
    """Проверяет токен и привязывает telegram_id к аккаунту, которому выдан токен."""
    token = await session.scalar(
        select(LinkToken).where(LinkToken.token_hash == _hash_token(raw_token))
    )
    if token is None:
        return LinkStatus.INVALID
    if token.used_at is not None:
        return LinkStatus.USED
    if token.expires_at < utcnow():
        return LinkStatus.EXPIRED

    user = await session.get(User, token.user_id)
    if user is None:
        return LinkStatus.INVALID

    # Повторное нажатие той же ссылкой тем же Telegram-аккаунтом: считаем успехом
    if user.telegram_id == telegram_id:
        token.used_at = utcnow()
        await session.commit()
        return LinkStatus.OK

    # Аккаунт сайта уже связан с другим Telegram или этот Telegram уже занят
    if user.telegram_id is not None:
        return LinkStatus.ALREADY_LINKED
    taken = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if taken is not None:
        return LinkStatus.ALREADY_LINKED

    user.telegram_id = telegram_id
    token.used_at = utcnow()
    await session.commit()
    return LinkStatus.OK


def build_link_url(bot_username: str, raw_token: str) -> str:
    """Ссылка deep link для открытия бота с токеном связки."""
    return f"https://t.me/{bot_username}?start={raw_token}"
