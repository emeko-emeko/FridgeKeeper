"""Вход на сайт через бота: подпись ссылки, маршрут /auth/bot-callback, ответ бота на /start login."""

import asyncio
import base64
import json
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from api import auth as auth_module
from app import app
from bot import handlers
from core import telegram_auth as ta
from core.i18n import TEXTS
from core.telegram_auth import (
    TelegramAuthError,
    build_bot_login_url,
    make_bot_login_token,
    verify_bot_login_token,
)

client = TestClient(app)


def test_token_roundtrip_returns_telegram_id():
    token = make_bot_login_token(42, now=1000)
    assert verify_bot_login_token(token, now=1100) == 42


def test_token_expires_after_five_minutes():
    token = make_bot_login_token(42, now=1000)
    with pytest.raises(TelegramAuthError, match="устарела"):
        verify_bot_login_token(token, now=1000 + ta.BOT_LOGIN_TTL_SECONDS + 1)


def test_tampered_payload_is_rejected():
    token = make_bot_login_token(42, now=1000)
    _, _, sig = token.rpartition(".")
    fake_payload = base64.urlsafe_b64encode(json.dumps({"tid": 999, "exp": 10**10}).encode()).decode()
    with pytest.raises(TelegramAuthError, match="подпись"):
        verify_bot_login_token(f"{fake_payload}.{sig}", now=1000)


@pytest.mark.parametrize("bad", ["", "nodot", "a.b"])
def test_malformed_token_is_rejected(bad):
    with pytest.raises(TelegramAuthError):
        verify_bot_login_token(bad, now=0)


def test_build_url_points_to_site_callback_and_token_is_valid():
    url = build_bot_login_url(42)
    parts = urlsplit(url)
    assert url.startswith(ta.SITE_URL + "/auth/bot-callback?")
    assert verify_bot_login_token(parse_qs(parts.query)["t"][0]) == 42


def test_bot_callback_sets_session_cookie_and_redirects(monkeypatch):
    async def fake_get_or_create_user(session, telegram_id):
        assert telegram_id == 42
        return SimpleNamespace(id=7)

    monkeypatch.setattr(auth_module, "get_or_create_user", fake_get_or_create_user)
    response = TestClient(app).get(
        "/auth/bot-callback", params={"t": make_bot_login_token(42)}, follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/app"
    cookie = response.headers["set-cookie"].lower()
    assert "fk_session=" in cookie and "httponly" in cookie and "secure" in cookie


def test_bot_callback_with_bad_token_goes_back_to_login():
    response = TestClient(app).get("/auth/bot-callback", params={"t": "bad"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login?err=bot"


def test_login_page_offers_bot_button_and_keeps_legacy_widget():
    text = client.get("/login?lang=ru").text
    assert "https://t.me/FridgeKeeper_MESSAGE_BOT?start=login" in text
    assert "oauth.telegram.org" in text  # старый вход на месте
    assert "login__legacy" in text


def test_login_page_shows_error_after_failed_bot_link():
    text = client.get("/login?lang=ru&err=bot").text
    assert TEXTS["ru"]["login_bot_error"] in text


def test_start_login_replies_with_signed_site_link():
    sent = []

    class FakeMessage:
        from_user = SimpleNamespace(id=42, first_name="Test")

        async def answer(self, text, reply_markup=None):
            sent.append((text, reply_markup))

    asyncio.run(handlers.cmd_start(FakeMessage(), SimpleNamespace(args="login")))

    assert len(sent) == 1
    text, keyboard = sent[0]
    assert text == handlers.LOGIN_PROMPT_TEXT
    button = keyboard.inline_keyboard[0][0]
    assert button.text == handlers.LOGIN_BUTTON_TEXT
    assert button.url.startswith(ta.SITE_URL + "/auth/bot-callback?")
