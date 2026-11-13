"""Проверка подписи данных Telegram: Login Widget (браузер) и Mini App (внутри Telegram)."""

import base64
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl, urlencode

from core.config import SITE_URL, TELEGRAM_TOKEN

MAX_AUTH_AGE_SECONDS = 24 * 60 * 60  # подпись действует сутки
BOT_LOGIN_TTL_SECONDS = 5 * 60  # ссылка «Войти на сайт» из бота живёт 5 минут


class TelegramAuthError(Exception):
    """Подпись неверна или данные устарели."""


def _check_string(fields: dict[str, str]) -> str:
    """Строка для подписи: пары key=value без hash, отсортированные по ключу, через перевод строки."""
    return "\n".join(f"{k}={v}" for k, v in sorted(fields.items()) if k != "hash")


def verify_login_widget(fields: dict[str, str]) -> int:
    """Проверяет данные из Telegram Login Widget и возвращает telegram_id.

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


def _check_age(auth_date: int) -> None:
    if time.time() - auth_date > MAX_AUTH_AGE_SECONDS:
        raise TelegramAuthError("Данные входа устарели, войдите снова")


# --- Вход через бота ---------------------------------------------------------
# Бот подписывает ссылку «Войти на сайт» для своего пользователя. Сайт проверяет подпись.
# Ключ — SHA-256 от строки с префиксом и токеном бота, поэтому ключ отличается от Login Widget.


def _bot_login_key() -> bytes:
    return hashlib.sha256(b"fk-bot-login:" + TELEGRAM_TOKEN.encode()).digest()


def make_bot_login_token(telegram_id: int, now: float | None = None) -> str:
    """Подписанный токен входа: payload.подпись. Вызывается ботом."""
    current = now if now is not None else time.time()
    exp = int(current + BOT_LOGIN_TTL_SECONDS)
    payload = base64.urlsafe_b64encode(json.dumps({"tid": telegram_id, "exp": exp}).encode()).decode()
    sig = hmac.new(_bot_login_key(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_bot_login_token(token: str, now: float | None = None) -> int:
    """Проверяет токен входа через бота и возвращает telegram_id. Вызывается сайтом."""
    if not token or "." not in token:
        raise TelegramAuthError("Ссылка входа повреждена")
    payload, _, sig = token.rpartition(".")
    expected = hmac.new(_bot_login_key(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise TelegramAuthError("Неверная подпись ссылки входа")
    try:
        data = json.loads(base64.urlsafe_b64decode(payload.encode()))
    except (ValueError, TypeError) as err:
        raise TelegramAuthError("Ссылка входа повреждена") from err
    if not isinstance(data.get("tid"), int):
        raise TelegramAuthError("Ссылка входа повреждена")
    current = now if now is not None else time.time()
    if data.get("exp", 0) < current:
        raise TelegramAuthError("Ссылка входа устарела, нажмите Start в боте ещё раз")
    return data["tid"]


def build_bot_login_url(telegram_id: int) -> str:
    """Адрес сайта, куда бот отправляет пользователя с токеном входа."""
    return f"{SITE_URL}/auth/bot-callback?" + urlencode({"t": make_bot_login_token(telegram_id)})