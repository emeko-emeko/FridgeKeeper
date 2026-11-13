"""Тесты входа на сайт через бота.

Поток: сайт создаёт код → /start login_<код> только показывает запрос с кнопками →
кнопка «Подтвердить» привязывает код к нажавшему, «Отмена» гасит код → сайт опрашивает статус.
"""

import base64
import hashlib
import hmac
import json
import re
import time
from datetime import datetime
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from aiogram.filters import CommandObject
from fastapi.testclient import TestClient
from sqlalchemy import select

from api.auth import SESSION_COOKIE, SESSION_SECRET, get_session, make_session_token, read_session
from app import app
from bot import handlers
from bot.formatting import LINK_MESSAGES, LOGIN_CALLBACK_MESSAGES, LOGIN_MESSAGES, login_confirm_text
from core.bot_login import (
    LOGIN_CODE_LENGTH,
    LOGIN_CODE_TTL_SECONDS,
    ConfirmStatus,
    cancel_login_by_id,
    check_login_code,
    confirm_login_by_id,
    create_login_code,
    inspect_login_code,
    is_login_code,
)
import core.telegram_auth as tg_auth
from core.database import init_db, make_session_factory
from core.i18n import TELEGRAM_BOT_URL
from core.telegram_auth import _check_string
from core.users import get_or_create_user, mark_bot_started
from models import LoginCode, User


@pytest_asyncio.fixture
async def factory(tmp_path):
    """Временная SQLite для эндпоинтов; сессия подменяет get_session приложения."""
    engine, factory = make_session_factory(f"sqlite+aiosqlite:///{tmp_path / 'login.db'}")
    await init_db(engine)

    async def override_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    yield factory
    app.dependency_overrides.clear()
    await engine.dispose()


def _fake_message(telegram_id: int, replies: list, markups: list):
    async def answer(text, **kwargs):
        replies.append(text)
        markups.append(kwargs.get("reply_markup"))

    return SimpleNamespace(from_user=SimpleNamespace(id=telegram_id, first_name="Тест"), answer=answer)


async def _send_start(monkeypatch, factory, telegram_id: int, args: str):
    """Имитирует /start <args>. Возвращает (тексты ответов, клавиатуры ответов)."""
    monkeypatch.setattr(handlers, "SessionFactory", factory)
    replies: list[str] = []
    markups: list = []
    message = _fake_message(telegram_id, replies, markups)
    await handlers.cmd_start(message, CommandObject(prefix="/", command="start", args=args))
    return replies, markups


async def _press(monkeypatch, factory, telegram_id: int, data: str) -> list[str]:
    """Имитирует нажатие inline-кнопки. Возвращает тексты ответов бота."""
    monkeypatch.setattr(handlers, "SessionFactory", factory)
    replies: list[str] = []
    markups: list = []

    async def noop(*args, **kwargs):
        return None

    message = SimpleNamespace(
        answer=_fake_message(telegram_id, replies, markups).answer,
        edit_reply_markup=noop,
    )
    callback = SimpleNamespace(
        from_user=SimpleNamespace(id=telegram_id),
        data=data,
        message=message,
        answer=noop,
    )
    await handlers.on_login_callback(callback)
    return replies


def _button_ids(markups: list) -> tuple[str, str]:
    """callback_data кнопок «Подтвердить» и «Отмена» из клавиатуры запроса."""
    keyboard = markups[0].inline_keyboard[0]
    return keyboard[0].callback_data, keyboard[1].callback_data


async def _start_via_bot(monkeypatch, factory, telegram_id: int, code: str):
    """/start login_<code> и возвращает (confirm_data, cancel_data) из ответа бота."""
    replies, markups = await _send_start(monkeypatch, factory, telegram_id, f"login_{code}")
    assert replies and "Подтвердить вход" in replies[0]
    return _button_ids(markups)


def _start_code(client: TestClient) -> str:
    response = client.post("/auth/bot-login/start")
    assert response.status_code == 200
    return response.json()["code"]


def _cookie_value(set_cookie: str) -> str:
    match = re.search(r"fk_session=([^;]+)", set_cookie)
    assert match, set_cookie
    # Starlette берёт значение в кавычки, если в нём есть «=» (base64); сервер кавычки снимает
    return match.group(1).strip('"')


async def _stored_row(factory, raw_code: str) -> LoginCode:
    async with factory() as s:
        _, row = await inspect_login_code(s, raw_code)
        assert row is not None
        return row


def test_start_returns_code_and_bot_link(factory):
    data = TestClient(app).post("/auth/bot-login/start").json()
    code = data["code"]

    assert len(code) == LOGIN_CODE_LENGTH
    assert data["bot_url"] == f"{TELEGRAM_BOT_URL}?start=login_{code}"
    assert len(f"login_{code}") <= 64  # лимит параметра /start в Telegram


def test_status_is_pending_before_bot_confirms(factory):
    client = TestClient(app)
    code = _start_code(client)

    response = client.get("/auth/bot-login/status", params={"code": code})
    assert response.json() == {"status": "pending"}
    assert "set-cookie" not in response.headers


@pytest.mark.asyncio
async def test_start_with_login_code_does_not_bind(factory, monkeypatch):
    """Главное: /start login_<код> не привязывает код, сайт по-прежнему видит pending."""
    client = TestClient(app)
    code = _start_code(client)

    replies, markups = await _send_start(monkeypatch, factory, 4241, f"login_{code}")
    assert len(replies) == 1
    assert "Подтвердить вход" in replies[0]
    assert "Отмена" in markups[0].inline_keyboard[0][1].text

    response = client.get("/auth/bot-login/status", params={"code": code})
    assert response.json() == {"status": "pending"}
    assert "set-cookie" not in response.headers
    row = await _stored_row(factory, code)
    assert row.confirmed_user_id is None
    assert row.used_at is None


@pytest.mark.asyncio
async def test_confirm_button_binds_and_site_gets_ok(factory, monkeypatch):
    client = TestClient(app)
    code = _start_code(client)
    confirm_data, _ = await _start_via_bot(monkeypatch, factory, 4242, code)

    replies = await _press(monkeypatch, factory, 4242, confirm_data)
    assert replies == [LOGIN_MESSAGES["ok"]]

    response = client.get("/auth/bot-login/status", params={"code": code})
    assert response.json() == {"status": "ok"}
    set_cookie = response.headers["set-cookie"]
    assert "httponly" in set_cookie.lower()
    assert "secure" in set_cookie.lower()
    assert "samesite=lax" in set_cookie.lower()

    user_id, bot_started = read_session(_cookie_value(set_cookie))
    assert bot_started is True
    async with factory() as s:
        user = await get_or_create_user(s, 4242)
        assert user_id == user.id


@pytest.mark.asyncio
async def test_cancel_button_gives_expired_for_site(factory, monkeypatch):
    client = TestClient(app)
    code = _start_code(client)
    _, cancel_data = await _start_via_bot(monkeypatch, factory, 4250, code)

    replies = await _press(monkeypatch, factory, 4250, cancel_data)
    assert replies == [LOGIN_CALLBACK_MESSAGES["cancelled"]]

    response = client.get("/auth/bot-login/status", params={"code": code})
    assert response.json() == {"status": "expired"}
    assert "set-cookie" not in response.headers


@pytest.mark.asyncio
async def test_repeat_confirm_is_safe_and_does_not_rebind(factory, monkeypatch):
    client = TestClient(app)
    code = _start_code(client)
    confirm_data, _ = await _start_via_bot(monkeypatch, factory, 4260, code)

    assert await _press(monkeypatch, factory, 4260, confirm_data) == [LOGIN_MESSAGES["ok"]]
    # Повтор тем же пользователем и нажатие другим аккаунтом: ничего не меняется
    assert await _press(monkeypatch, factory, 4260, confirm_data) == [LOGIN_MESSAGES["used"]]
    assert await _press(monkeypatch, factory, 4261, confirm_data) == [LOGIN_MESSAGES["used"]]

    first = client.get("/auth/bot-login/status", params={"code": code})
    assert first.json() == {"status": "ok"}
    assert client.get("/auth/bot-login/status", params={"code": code}).json() == {"status": "expired"}
    row = await _stored_row(factory, code)
    async with factory() as s:
        owner = await get_or_create_user(s, 4260)
    assert row.confirmed_user_id == owner.id


@pytest.mark.asyncio
async def test_confirm_after_cancel_is_used_and_site_stays_expired(factory, monkeypatch):
    client = TestClient(app)
    code = _start_code(client)
    confirm_data, cancel_data = await _start_via_bot(monkeypatch, factory, 4270, code)

    assert await _press(monkeypatch, factory, 4270, cancel_data) == [LOGIN_CALLBACK_MESSAGES["cancelled"]]
    assert await _press(monkeypatch, factory, 4270, confirm_data) == [LOGIN_MESSAGES["used"]]
    assert await _press(monkeypatch, factory, 4270, cancel_data) == [LOGIN_MESSAGES["used"]]

    response = client.get("/auth/bot-login/status", params={"code": code})
    assert response.json() == {"status": "expired"}
    assert "set-cookie" not in response.headers


@pytest.mark.asyncio
async def test_unknown_or_foreign_id_is_safe(factory, monkeypatch):
    """Нажатие по несуществующему id, с битым callback и с чужим id не падает и ничего не меняет."""
    assert await _press(monkeypatch, factory, 4280, "login:ok:999999") == [LOGIN_MESSAGES["invalid"]]
    assert await _press(monkeypatch, factory, 4280, "login:no:999999") == [LOGIN_MESSAGES["invalid"]]
    assert await _press(monkeypatch, factory, 4280, "login:ok:abc") == []
    assert await _press(monkeypatch, factory, 4280, "login:drop:1") == []
    assert await _press(monkeypatch, factory, 4280, "login:ok") == []


@pytest.mark.asyncio
async def test_expired_code_start_and_buttons(factory, monkeypatch):
    async with factory() as s:
        raw = await create_login_code(s, ttl_seconds=-1)
        _, row = await inspect_login_code(s, raw)
        login_id = row.id

    assert await _send_start(monkeypatch, factory, 4290, f"login_{raw}") == (
        [LOGIN_MESSAGES["expired"]],
        [None],
    )
    assert await _press(monkeypatch, factory, 4290, f"login:ok:{login_id}") == [LOGIN_MESSAGES["expired"]]
    assert await _press(monkeypatch, factory, 4290, f"login:no:{login_id}") == [LOGIN_MESSAGES["expired"]]


@pytest.mark.asyncio
async def test_unknown_code_is_expired_for_site_and_invalid_for_bot(factory, monkeypatch):
    client = TestClient(app)
    fake = "x" * LOGIN_CODE_LENGTH

    response = client.get("/auth/bot-login/status", params={"code": fake})
    assert response.json() == {"status": "expired"}
    assert "set-cookie" not in response.headers

    replies, _ = await _send_start(monkeypatch, factory, 4245, f"login_{fake}")
    assert replies == [LOGIN_MESSAGES["invalid"]]


@pytest.mark.asyncio
async def test_short_login_prefix_goes_to_link_branch(factory, monkeypatch):
    """Аргумент с префиксом login_, но не 43 символа, — это обычный link-токен."""
    assert not is_login_code("short")
    replies, _ = await _send_start(monkeypatch, factory, 4246, "login_short")
    assert replies == [LINK_MESSAGES["invalid"]]


def test_is_login_code_checks_length():
    assert is_login_code("a" * 43)
    assert not is_login_code("a" * 42)
    assert not is_login_code("a" * 44)
    assert not is_login_code("")


def test_status_without_code_is_expired(factory):
    response = TestClient(app).get("/auth/bot-login/status")
    assert response.json() == {"status": "expired"}


def test_ttl_is_five_minutes():
    assert LOGIN_CODE_TTL_SECONDS == 300


def test_confirm_text_shows_time_in_almaty():
    # 00:00 UTC = 05:00 по Астане (UTC+5)
    text = login_confirm_text(datetime(2026, 11, 13, 0, 0))
    assert "13.11.2026 05:00" in text
    assert "Отмена" in text


@pytest.mark.asyncio
async def test_create_stores_created_at(session):
    raw = await create_login_code(session)
    _, row = await inspect_login_code(session, raw)
    assert row.created_at is not None
    assert row.expires_at > row.created_at


@pytest.mark.asyncio
async def test_expired_code_is_rejected_by_site_and_bot(session):
    raw = await create_login_code(session, ttl_seconds=-1)
    _, row = await inspect_login_code(session, raw)

    assert await check_login_code(session, raw) == ("expired", None)
    assert await confirm_login_by_id(session, row.id, telegram_id=5001) is ConfirmStatus.EXPIRED
    assert await cancel_login_by_id(session, row.id) is ConfirmStatus.EXPIRED


@pytest.mark.asyncio
async def test_core_inspect_does_not_bind(session):
    raw = await create_login_code(session)
    status, row = await inspect_login_code(session, raw)
    assert status is ConfirmStatus.PENDING
    assert await check_login_code(session, raw) == ("pending", None)
    # Повторный осмотр не меняет состояние
    status_again, _ = await inspect_login_code(session, raw)
    assert status_again is ConfirmStatus.PENDING


@pytest.mark.asyncio
async def test_core_confirm_then_check_returns_user_once(session):
    user = await get_or_create_user(session, 5002)
    raw = await create_login_code(session)
    _, row = await inspect_login_code(session, raw)

    assert await check_login_code(session, raw) == ("pending", None)
    assert await confirm_login_by_id(session, row.id, telegram_id=5002) is ConfirmStatus.OK
    assert await check_login_code(session, raw) == ("ok", user.id)
    assert await check_login_code(session, raw) == ("expired", None)


@pytest.mark.asyncio
async def test_confirm_twice_is_used(session):
    raw = await create_login_code(session)
    _, row = await inspect_login_code(session, raw)
    assert await confirm_login_by_id(session, row.id, telegram_id=5003) is ConfirmStatus.OK
    assert await confirm_login_by_id(session, row.id, telegram_id=5004) is ConfirmStatus.USED


@pytest.mark.asyncio
async def test_cancel_then_check_is_expired(session):
    raw = await create_login_code(session)
    _, row = await inspect_login_code(session, raw)
    assert await cancel_login_by_id(session, row.id) is ConfirmStatus.CANCELLED
    assert await check_login_code(session, raw) == ("expired", None)
    assert await confirm_login_by_id(session, row.id, telegram_id=5005) is ConfirmStatus.USED


@pytest.mark.asyncio
async def test_code_is_stored_only_as_hash(session):
    raw = await create_login_code(session)
    stored = (await session.scalars(select(LoginCode))).all()
    assert len(stored) == 1
    assert stored[0].code_hash != raw
    assert stored[0].code_hash == hashlib.sha256(raw.encode()).hexdigest()


async def _user_id(factory, telegram_id: int) -> int:
    async with factory() as s:
        return (await get_or_create_user(s, telegram_id)).id


async def _bot_started_at(factory, user_id: int):
    async with factory() as s:
        user = await s.get(User, user_id)
        return user.bot_started_at


def _cookie_headers(token: str) -> dict[str, str]:
    return {"cookie": f"{SESSION_COOKIE}={token}"}


def _bearer_headers(token: str) -> dict[str, str]:
    return {"authorization": f"Bearer {token}"}


def test_me_ignores_bs_claim_in_token(factory):
    """Claim bs в токене больше не влияет на /auth/me: решает только БД. Пользователя 7 в БД нет."""
    token = make_session_token(7, bot_started=True)
    response = TestClient(app).get("/auth/me", headers=_cookie_headers(token))
    assert response.status_code == 200
    assert response.json() == {"user_id": 7, "bot_started": False}


@pytest.mark.asyncio
async def test_me_with_widget_token_reports_bot_started_false(factory):
    uid = await _user_id(factory, 4310)
    token = make_session_token(uid)
    response = TestClient(app).get("/auth/me", headers=_cookie_headers(token))
    assert response.json() == {"user_id": uid, "bot_started": False}


@pytest.mark.asyncio
async def test_me_with_bearer_token_reports_db_value(factory, monkeypatch):
    uid = await _user_id(factory, 4311)
    token = make_session_token(uid)
    client = TestClient(app)
    assert client.get("/auth/me", headers=_bearer_headers(token)).json() == {"user_id": uid, "bot_started": False}
    await _send_start(monkeypatch, factory, 4311, "")
    assert client.get("/auth/me", headers=_bearer_headers(token)).json() == {"user_id": uid, "bot_started": True}


def test_me_without_session_is_401(factory):
    assert TestClient(app).get("/auth/me").status_code == 401


def _signed_widget_fields(telegram_id: int, token: str) -> dict[str, str]:
    fields = {"id": str(telegram_id), "first_name": "Тест", "auth_date": str(int(time.time()))}
    secret = hashlib.sha256(token.encode()).digest()
    fields["hash"] = hmac.new(secret, _check_string(fields).encode(), hashlib.sha256).hexdigest()
    return fields


@pytest.mark.asyncio
async def test_widget_login_then_start_in_bot_same_session(factory, monkeypatch):
    """Вход виджетом: false. После /start в боте та же cookie сразу даёт true, без перелогина."""
    monkeypatch.setattr(tg_auth, "TELEGRAM_TOKEN", "123:TEST")
    client = TestClient(app)
    query = urlencode(_signed_widget_fields(4320, "123:TEST"))
    login = client.get(f"/auth/login-widget?{query}", follow_redirects=False)
    assert login.status_code == 303
    token = _cookie_value(login.headers["set-cookie"])

    assert client.get("/auth/me", headers=_cookie_headers(token)).json()["bot_started"] is False

    await _send_start(monkeypatch, factory, 4320, "")
    me = client.get("/auth/me", headers=_cookie_headers(token)).json()
    assert me["bot_started"] is True
    assert me["user_id"] == await _user_id(factory, 4320)


@pytest.mark.asyncio
async def test_login_through_bot_gives_bot_started_true(factory, monkeypatch):
    client = TestClient(app)
    code = _start_code(client)
    confirm_data, _ = await _start_via_bot(monkeypatch, factory, 4330, code)
    assert await _press(monkeypatch, factory, 4330, confirm_data) == [LOGIN_MESSAGES["ok"]]

    response = client.get("/auth/bot-login/status", params={"code": code})
    token = _cookie_value(response.headers["set-cookie"])
    assert client.get("/auth/me", headers=_cookie_headers(token)).json() == {
        "user_id": await _user_id(factory, 4330),
        "bot_started": True,
    }


@pytest.mark.asyncio
async def test_mini_app_session_true_after_start(factory, monkeypatch):
    import api.auth as auth_module

    monkeypatch.setattr(auth_module, "verify_mini_app", lambda init_data: 4340)
    client = TestClient(app)
    token = client.post("/auth/mini-app", json={"init_data": "x"}).json()["token"]

    assert client.get("/auth/me", headers=_bearer_headers(token)).json()["bot_started"] is False
    await _send_start(monkeypatch, factory, 4340, "")
    assert client.get("/auth/me", headers=_bearer_headers(token)).json()["bot_started"] is True


@pytest.mark.asyncio
async def test_link_token_start_marks_bot_started(factory, monkeypatch):
    uid = await _user_id(factory, 4350)
    token = make_session_token(uid)
    client = TestClient(app)
    assert client.get("/auth/me", headers=_cookie_headers(token)).json()["bot_started"] is False

    await _send_start(monkeypatch, factory, 4350, "not-a-real-link-token")
    assert client.get("/auth/me", headers=_cookie_headers(token)).json()["bot_started"] is True


@pytest.mark.asyncio
async def test_start_for_new_telegram_user_creates_marked_row(factory, monkeypatch):
    await _send_start(monkeypatch, factory, 4360, "")
    uid = await _user_id(factory, 4360)
    assert await _bot_started_at(factory, uid) is not None


@pytest.mark.asyncio
async def test_bot_started_at_is_set_once(factory, monkeypatch):
    await _send_start(monkeypatch, factory, 4370, "")
    uid = await _user_id(factory, 4370)
    first = await _bot_started_at(factory, uid)
    assert first is not None

    await _send_start(monkeypatch, factory, 4370, "")
    assert await _bot_started_at(factory, uid) == first


@pytest.mark.asyncio
async def test_mark_bot_started_core(session):
    user = await get_or_create_user(session, 4380)
    assert user.bot_started_at is None
    await mark_bot_started(session, 4380)
    assert user.bot_started_at is not None
    first = user.bot_started_at
    await mark_bot_started(session, 4380)
    assert user.bot_started_at == first


def test_unknown_user_id_reports_not_started(factory):
    token = make_session_token(999999)
    response = TestClient(app).get("/auth/me", headers=_cookie_headers(token))
    assert response.json() == {"user_id": 999999, "bot_started": False}


def test_me_without_session_is_401(factory):
    assert TestClient(app).get("/auth/me").status_code == 401


def test_token_without_bot_claim_reads_as_not_started():
    """Токены, выданные до появления поля bs, читаются как bot_started = False."""
    payload = base64.urlsafe_b64encode(json.dumps({"uid": 11, "exp": 4102444800}).encode()).decode()
    sig = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    assert read_session(f"{payload}.{sig}") == (11, False)
