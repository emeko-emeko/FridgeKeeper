"""Проверка подписи данных Telegram: Login Widget (браузер) и Mini App (внутри Telegram)."""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from core.config import TELEGRAM_TOKEN

MAX_AUTH_AGE_SECONDS = 24 * 60 * 60  # подпись действует сутки


class TelegramAuthError(Exception):
    """Подпись неверна или данные устарели."""


def _check_string(fields: dict[str, str]) -> str:
    """Строка для подписи: пары key=value без hash, отсортированные по ключу, через перевод строки."""
    return "\n".join(f"{k}={v}" for k, v in sorted(fields.items()) if k != "hash")


def verify_login_widget(fields: dict[str, str]) -> int:
    """НЕ УДАЛЯТЬ: запасной вход через Telegram Login Widget (решение пользователя 13.11.2026).

    Проверяет данные из Telegram Login Widget и возвращает telegram_id.

    Ключ подписи — SHA-256 от токена бота.
    """
    received_hash = fields.get("hash", "")
    secret = hashlib.sha256(TELEGRAM_TOKEN.encode()).digest()
    expected = hmac.new(secret, _check_string(fields).encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        raise TelegramAuthError("Неверная подпись Login Widget")
    _check_age(int(fields.get("auth_date", "0")))
    return int(fields["id"])


def verify_mini_app(init_data: str) -> int:
    """Проверяет initData из Telegram Mini App и возвращает telegram_id.

    Ключ подписи — HMAC-SHA256 от токена бота с ключом "WebAppData".
    """
    fields = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = fields.get("hash", "")
    secret = hmac.new(b"WebAppData", TELEGRAM_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, _check_string(fields).encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        raise TelegramAuthError("Неверная подпись Mini App")
    _check_age(int(fields.get("auth_date", "0")))

    user = json.loads(fields.get("user", "{}"))
    if "id" not in user:
        raise TelegramAuthError("В initData нет пользователя")
    return int(user["id"])


def mini_app_first_name(init_data: str) -> str | None:
    """Имя пользователя из initData. Вызывать после verify_mini_app: подпись здесь не проверяется.

    Любой разбор с ошибкой даёт None, а не исключение: имя не обязательно для входа.
    """
    try:
        fields = dict(parse_qsl(init_data, keep_blank_values=True))
        user = json.loads(fields.get("user", "{}"))
    except (ValueError, TypeError):
        return None
    name = user.get("first_name") if isinstance(user, dict) else None
    return name if isinstance(name, str) else None


def _check_age(auth_date: int) -> None:
    if time.time() - auth_date > MAX_AUTH_AGE_SECONDS:
        raise TelegramAuthError("Данные входа устарели, войдите снова")