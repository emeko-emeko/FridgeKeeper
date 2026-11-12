import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from core import telegram_auth
from core.telegram_auth import TelegramAuthError, verify_login_widget, verify_mini_app

TOKEN = "123456:TEST_TOKEN"


@pytest.fixture(autouse=True)
def fake_token(monkeypatch):
    monkeypatch.setattr(telegram_auth, "TELEGRAM_TOKEN", TOKEN)


def _sign_widget(fields: dict) -> dict:
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hashlib.sha256(TOKEN.encode()).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return fields


def _sign_mini_app(fields: dict) -> str:
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_widget_valid_signature_returns_telegram_id():
    fields = _sign_widget({"id": "42", "first_name": "Ann", "auth_date": str(int(time.time()))})
    assert verify_login_widget(fields) == 42


def test_widget_tampered_field_is_rejected():
    fields = _sign_widget({"id": "42", "auth_date": str(int(time.time()))})
    fields["id"] = "43"
    with pytest.raises(TelegramAuthError):
        verify_login_widget(fields)


def test_widget_old_auth_date_is_rejected():
    old = str(int(time.time()) - 2 * 24 * 3600)
    fields = _sign_widget({"id": "42", "auth_date": old})
    with pytest.raises(TelegramAuthError):
        verify_login_widget(fields)


def test_mini_app_valid_signature_returns_user_id():
    user = json.dumps({"id": 77, "first_name": "Bob"})
    init_data = _sign_mini_app({"auth_date": str(int(time.time())), "user": user})
    assert verify_mini_app(init_data) == 77


def test_mini_app_wrong_token_is_rejected(monkeypatch):
    user = json.dumps({"id": 77})
    init_data = _sign_mini_app({"auth_date": str(int(time.time())), "user": user})
    monkeypatch.setattr(telegram_auth, "TELEGRAM_TOKEN", "other:token")
    with pytest.raises(TelegramAuthError):
        verify_mini_app(init_data)