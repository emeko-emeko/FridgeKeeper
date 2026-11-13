"""Вход на сайт через бота: код выдаёт бот, вводит его человек на сайте.

Поток:
1. Пользователь пишет боту /login (или /start login). Бот создаёт код XXXX-XXXX, привязанный
   к telegram_id этого пользователя, и показывает его только в его чате.
   Прежние неиспользованные коды пользователя гасятся.
2. Пользователь вводит код на сайте. verify_bot_code() ищет строку по SHA-256 хэшу,
   помечает код использованным одним условным UPDATE и возвращает user_id.

Сайт код не создаёт и не привязывает, поэтому ссылку с кодом нельзя подсунуть жертве.
В БД хранится только хэш. Код живёт в таблице login_codes (миграция 0002).
"""

import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.users import get_or_create_user
from models import LoginCode, utcnow

LOGIN_CODE_TTL_SECONDS = 5 * 60  # код действует 5 минут
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # без I, O, 0, 1: не путаются при чтении
CODE_LENGTH = 8  # 32^8 ≈ 1.1e12 вариантов


def normalize_code(raw: str) -> str:
    """Приводит введённый код к виду без пробелов и дефисов, в верхнем регистре."""
    return "".join((raw or "").split()).replace("-", "").upper()


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _format_code(code: str) -> str:
    return f"{code[:4]}-{code[4:]}"


def generate_code() -> str:
    """Случайный код из 8 символов алфавита CODE_ALPHABET (через secrets)."""
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


async def create_bot_login_code(
    session: AsyncSession, telegram_id: int, ttl_seconds: int = LOGIN_CODE_TTL_SECONDS
) -> str:
    """Создаёт код для пользователя и возвращает его открытое значение в виде XXXX-XXXX.

    Вызывается только из обработчика бота: telegram_id берётся из сообщения пользователя.
    """
    user = await get_or_create_user(session, telegram_id)
    now = utcnow()
    # Гасим прежние неиспользованные коды этого пользователя: действует только последний
    await session.execute(
        update(LoginCode)
        .where(LoginCode.confirmed_user_id == user.id, LoginCode.used_at.is_(None))
        .values(used_at=now)
    )
    code = generate_code()
    session.add(
        LoginCode(
            code_hash=_hash_code(code),
            created_at=now,
            confirmed_user_id=user.id,
            confirmed_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
    )
    await session.commit()
    return _format_code(code)


async def verify_bot_code(session: AsyncSession, raw: str) -> int | None:
    """Проверяет код, введённый на сайте. Возвращает user_id или None.

    Неверный, истёкший, использованный и неполный код дают один и тот же результат None.
    Код помечается использованным условным UPDATE: повторный ввод или параллельный запрос не пройдут.
    """
    code = normalize_code(raw)
    if len(code) != CODE_LENGTH or any(ch not in CODE_ALPHABET for ch in code):
        return None

    now = utcnow()
    row = await session.scalar(select(LoginCode).where(LoginCode.code_hash == _hash_code(code)))
    if row is None or row.used_at is not None or row.confirmed_user_id is None or row.expires_at < now:
        return None

    row_id = row.id
    user_id = row.confirmed_user_id  # до commit: после него атрибуты строки могут быть недоступны
    result = await session.execute(
        update(LoginCode)
        .where(
            LoginCode.id == row_id,
            LoginCode.used_at.is_(None),
            LoginCode.confirmed_user_id.is_not(None),
            LoginCode.expires_at >= now,
        )
        .values(used_at=utcnow())
    )
    await session.commit()
    if result.rowcount != 1:
        return None
    return user_id
