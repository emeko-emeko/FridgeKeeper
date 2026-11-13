"""Вход на сайт через бота.

Поток:
1. Сайт вызывает create_login_code() и отдаёт браузеру код и ссылку t.me/<бот>?start=login_<код>.
2. Пользователь открывает ссылку. /start login_<код> только показывает запрос с кнопками
   «Подтвердить» / «Отмена» (inspect_login_code, код НЕ привязывается).
3. Привязка делается только по нажатию «Подтвердить» (confirm_login_by_id, telegram_id из
   callback). «Отмена» (cancel_login_by_id) гасит код.
4. Страница сайта опрашивает check_login_code(). Когда код подтверждён, выдаётся cookie и код гаснет.

Код хранится в БД (не в памяти процесса), поэтому работает на любом инстансе Vercel.
"""

import hashlib
import hmac
import secrets
from datetime import timedelta
from enum import Enum

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.users import get_or_create_user
from models import LoginCode, utcnow

LOGIN_CODE_TTL_SECONDS = 5 * 60  # код действует 5 минут
START_PREFIX = "login_"  # параметр /start: login_<код>
LOGIN_CODE_LENGTH = 43  # token_urlsafe(32) даёт ровно 43 символа
NONCE_LENGTH = 16  # первые hex-символы code_hash; кладутся в callback_data кнопок


class ConfirmStatus(Enum):
    """Состояние кода входа и результат действий бота."""

    OK = "ok"              # подтверждён этим нажатием
    INVALID = "invalid"    # код не найден
    EXPIRED = "expired"    # срок истёк
    USED = "used"          # уже подтверждён или отменён / использован
    PENDING = "pending"    # ждёт подтверждения (только для inspect_login_code)
    CANCELLED = "cancelled"  # пользователь нажал «Отмена»


def is_login_code(code: str) -> bool:
    """Похоже ли значение на код входа (а не на link-токен из /start)."""
    return len(code) == LOGIN_CODE_LENGTH


def _hash_code(raw_code: str) -> str:
    return hashlib.sha256(raw_code.encode("utf-8")).hexdigest()


def login_nonce(row: LoginCode) -> str:
    """Нонс строки для callback_data кнопок: префикс уже хранимого code_hash, секрет не раскрывает."""
    return row.code_hash[:NONCE_LENGTH]


def _nonce_matches(row: LoginCode, nonce: str) -> bool:
    """Сравнение нонса с code_hash строки за постоянное время."""
    return hmac.compare_digest(login_nonce(row).encode("utf-8"), nonce.encode("utf-8"))


def _state(row: LoginCode) -> ConfirmStatus:
    """Состояние строки без изменения БД."""
    if row.used_at is not None or row.confirmed_user_id is not None:
        return ConfirmStatus.USED
    if row.expires_at < utcnow():
        return ConfirmStatus.EXPIRED
    return ConfirmStatus.PENDING


async def _find(session: AsyncSession, raw_code: str) -> LoginCode | None:
    if not raw_code:
        return None
    return await session.scalar(select(LoginCode).where(LoginCode.code_hash == _hash_code(raw_code)))


async def _find_by_id(session: AsyncSession, login_code_id: int) -> LoginCode | None:
    # populate_existing: состояние берём из БД, а не из кэша сессии
    return await session.scalar(
        select(LoginCode).where(LoginCode.id == login_code_id).execution_options(populate_existing=True)
    )


async def create_login_code(session: AsyncSession, ttl_seconds: int = LOGIN_CODE_TTL_SECONDS) -> str:
    """Создаёт код входа и возвращает его открытое значение (256 бит, urlsafe).

    Длина 43 символа + префикс «login_» укладывается в лимит 64 символа параметра /start.
    """
    raw_code = secrets.token_urlsafe(32)
    now = utcnow()
    session.add(
        LoginCode(
            code_hash=_hash_code(raw_code),
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
    )
    await session.commit()
    return raw_code


async def inspect_login_code(session: AsyncSession, raw_code: str) -> tuple[ConfirmStatus, LoginCode | None]:
    """Вызывается при /start login_<код>. Ничего не меняет в БД.

    Возвращает PENDING (можно показать кнопки), INVALID, EXPIRED или USED и строку кода.
    """
    row = await _find(session, raw_code)
    if row is None:
        return ConfirmStatus.INVALID, None
    return _state(row), row


async def confirm_login_by_id(
    session: AsyncSession, login_code_id: int, telegram_id: int, nonce: str
) -> ConfirmStatus:
    """Вызывается только из кнопки «Подтвердить». Привязывает код к telegram_id нажавшего.

    Без совпадения нонса (защита от подбора id и login CSRF) возвращает INVALID и ничего не меняет.
    """
    row = await _find_by_id(session, login_code_id)
    if row is None or not _nonce_matches(row, nonce):
        return ConfirmStatus.INVALID
    status = _state(row)
    if status is not ConfirmStatus.PENDING:
        return status

    row_id = row.id  # до commit: после него атрибуты строки могут быть недоступны
    user = await get_or_create_user(session, telegram_id)
    # Условное обновление: повторное или параллельное нажатие не подтвердит код дважды
    result = await session.execute(
        update(LoginCode)
        .where(
            LoginCode.id == row_id,
            LoginCode.confirmed_user_id.is_(None),
            LoginCode.used_at.is_(None),
            LoginCode.expires_at >= utcnow(),
        )
        .values(confirmed_user_id=user.id, confirmed_at=utcnow())
    )
    await session.commit()
    if result.rowcount != 1:
        fresh = await _find_by_id(session, row_id)
        if fresh is None:
            return ConfirmStatus.INVALID
        fresh_status = _state(fresh)
        return fresh_status if fresh_status is not ConfirmStatus.PENDING else ConfirmStatus.USED
    return ConfirmStatus.OK


async def cancel_login_by_id(session: AsyncSession, login_code_id: int, nonce: str) -> ConfirmStatus:
    """Вызывается из кнопки «Отмена». Гасит код: сайт при опросе получит «expired».

    Без совпадения нонса возвращает INVALID и ничего не меняет.
    """
    row = await _find_by_id(session, login_code_id)
    if row is None or not _nonce_matches(row, nonce):
        return ConfirmStatus.INVALID
    status = _state(row)
    if status is not ConfirmStatus.PENDING:
        return status

    row_id = row.id
    result = await session.execute(
        update(LoginCode)
        .where(
            LoginCode.id == row_id,
            LoginCode.confirmed_user_id.is_(None),
            LoginCode.used_at.is_(None),
        )
        .values(used_at=utcnow())
    )
    await session.commit()
    if result.rowcount != 1:
        return ConfirmStatus.USED
    return ConfirmStatus.CANCELLED


async def check_login_code(session: AsyncSession, raw_code: str) -> tuple[str, int | None]:
    """Опрос со стороны сайта. Возвращает («pending»|«ok»|«expired», user_id или None).

    При «ok» код помечается использованным атомарно: второй опрос получит «expired».
    """
    row = await _find(session, raw_code)
    if row is None or row.used_at is not None:
        return "expired", None
    if row.expires_at < utcnow():
        return "expired", None
    if row.confirmed_user_id is None:
        return "pending", None

    user_id = row.confirmed_user_id
    result = await session.execute(
        update(LoginCode)
        .where(LoginCode.id == row.id, LoginCode.used_at.is_(None))
        .values(used_at=utcnow())
    )
    await session.commit()
    if result.rowcount != 1:
        return "expired", None
    return "ok", user_id
