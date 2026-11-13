"""Тесты входа на сайт через бота.

Поток: пользователь пишет боту /login (или /start login) → бот выдаёт код XXXX-XXXX этому пользователю →
пользователь вводит код на сайте → POST /auth/bot-login/verify ставит cookie.
Сайт код не создаёт, ссылок с кодом нет.
"""

import base64
import hashlib
import hmac
import json
import re
import time
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from aiogram.filters import CommandObject
from fastapi.testclient import TestClient
from sqlalchemy import select

import core.telegram_auth as tg_auth
from api.auth import SESSION_COOKIE, SESSION_SECRET, get_session, make_session_token, read_session
from app import app
from bot import handlers
from bot.formatting import BOT_COMMANDS, HELP_TEXT, LINK_MESSAGES
from core.bot_login import (
    CODE_ALPHABET,
    CODE_LENGTH,
    LOGIN_CODE_TTL_SECONDS,
    create_bot_login_code,
    generate_code,
)
from core.database import init_db, make_session_factory
from core.telegram_auth import _check_string
from core.users import get_or_create_user, mark_bot_started
from models import LoginCode, User

CODE_IN_TEXT = re.compile(r"<code>([A-Z0-9]{4}-[A-Z0-9]{4})</code>")
CODE_FORMAT = re.compile(r"[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}")
VERIFY_ERROR = "Код не подошёл или истёк"


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


def _fake_message(telegram_id: int, replies: list):
    async def answer(text, **kwargs):
        replies.append(text)

    return SimpleNamespace(from_user=SimpleNamespace(id=telegram_id, first_name="Тест"), answer=answer)


async def _login_command(monkeypatch, factory, telegram_id: int) -> str:
    """Вызывает /login и возвращает код из ответа бота (XXXX-XXXX)."""
    monkeypatch.setattr(handlers, "SessionFactory", factory)
    replies: list[str] = []
    await handlers.cmd_login(_fake_message(telegram_id, replies))
    assert len(replies) == 1
    match = CODE_IN_TEXT.search(replies[0])
    assert match, replies[0]
    return match.group(1)


async def _send_start(monkeypatch, factory, telegram_id: int, args: str) -> list[str]:
    """Имитирует /start <args>. Возвращает тексты ответов."""
    monkeypatch.setattr(handlers, "SessionFactory", factory)
    replies: list[str] = []
    message = _fake_message(telegram_id, replies)
    await handlers.cmd_start(message, CommandObject(prefix="/", command="start", args=args))
    return replies


def _verify(client: TestClient, code: str):
    return client.post("/auth/bot-login/verify", json={"code": code})


def _cookie_value(set_cookie: str) -> str:
    match = re.search(r"fk_session=([^;]+)", set_cookie)
    assert match, set_cookie
    # Starlette берёт значение в кавычки, если в нём есть «=» (base64); сервер кавычки снимает
    return match.group(1).strip('"')


def _cookie_headers(token: str) -> dict[str, str]:
    return {"cookie": f"{SESSION_COOKIE}={token}"}


def _bearer_headers(token: str) -> dict[str, str]:
    return {"authorization": f"Bearer {token}"}


async def _user_id(factory, telegram_id: int) -> int:
    async with factory() as s:
        return (await get_or_create_user(s, telegram_id)).id


async def _bot_started_at(factory, user_id: int):
    async with factory() as s:
        user = await s.get(User, user_id)
        return user.bot_started_at


# --- Выдача кода в боте ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_command_issues_code_in_format(factory, monkeypatch):
    code = await _login_command(monkeypatch, factory, 4500)
    assert CODE_FORMAT.fullmatch(code), code


@pytest.mark.asyncio
async def test_db_stores_only_hash_of_normalized_code(factory, monkeypatch):
    code = await _login_command(monkeypatch, factory, 4501)
    plain = code.replace("-", "")

    async with factory() as s:
        rows = (await s.scalars(select(LoginCode))).all()
        owner = await get_or_create_user(s, 4501)
    assert len(rows) == 1
    row = rows[0]
    assert row.code_hash == hashlib.sha256(plain.encode()).hexdigest()
    assert plain not in row.code_hash and code not in row.code_hash
    assert row.confirmed_user_id == owner.id
    assert row.used_at is None
    lifetime = (row.expires_at - row.created_at).total_seconds()
    assert abs(lifetime - LOGIN_CODE_TTL_SECONDS) < 1


@pytest.mark.asyncio
async def test_login_command_marks_bot_started(factory, monkeypatch):
    await _login_command(monkeypatch, factory, 4502)
    uid = await _user_id(factory, 4502)
    assert await _bot_started_at(factory, uid) is not None


@pytest.mark.asyncio
async def test_login_message_text_has_warning(factory, monkeypatch):
    monkeypatch.setattr(handlers, "SessionFactory", factory)
    replies: list[str] = []
    await handlers.cmd_login(_fake_message(4503, replies))
    text = replies[0]
    assert "5 минут" in text
    assert "Никому не сообщайте этот код и не вводите его нигде, кроме сайта FridgeKeeper" in text


@pytest.mark.asyncio
async def test_start_login_argument_issues_code(factory, monkeypatch):
    replies = await _send_start(monkeypatch, factory, 4510, "login")
    assert len(replies) == 1
    assert CODE_IN_TEXT.search(replies[0])
    uid = await _user_id(factory, 4510)
    assert await _bot_started_at(factory, uid) is not None


@pytest.mark.asyncio
async def test_old_login_prefix_start_issues_no_code(factory, monkeypatch):
    """Старый параметр login_<код> больше не работает: это обычный link-токен, кода не будет."""
    assert await _send_start(monkeypatch, factory, 4511, "login_" + "A" * 43) == [LINK_MESSAGES["invalid"]]
    assert await _send_start(monkeypatch, factory, 4511, "login_ABCD-EFGH") == [LINK_MESSAGES["invalid"]]
    async with factory() as s:
        assert (await s.scalars(select(LoginCode))).all() == []


@pytest.mark.asyncio
async def test_new_code_revokes_previous_code_of_same_user(factory, monkeypatch):
    client = TestClient(app)
    first = await _login_command(monkeypatch, factory, 4520)
    second = await _login_command(monkeypatch, factory, 4520)

    assert _verify(client, first).status_code == 400
    assert _verify(client, second).status_code == 200


@pytest.mark.asyncio
async def test_codes_of_different_users_do_not_revoke_each_other(factory, monkeypatch):
    client = TestClient(app)
    code_a = await _login_command(monkeypatch, factory, 4530)
    code_b = await _login_command(monkeypatch, factory, 4531)

    assert _verify(client, code_a).status_code == 200
    assert _verify(client, code_b).status_code == 200


def test_generated_codes_use_only_allowed_alphabet():
    assert len(CODE_ALPHABET) == 32
    assert not set("IO01") & set(CODE_ALPHABET)
    for _ in range(500):
        code = generate_code()
        assert len(code) == CODE_LENGTH
        assert set(code) <= set(CODE_ALPHABET)


# --- Проверка кода на сайте -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_with_code_sets_cookie_and_session_is_bot_started(factory, monkeypatch):
    code = await _login_command(monkeypatch, factory, 4540)
    client = TestClient(app)

    response = _verify(client, code)
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "secure" in set_cookie
    assert "samesite=lax" in set_cookie

    token = _cookie_value(response.headers["set-cookie"])
    user_id, bot_started = read_session(token)
    assert bot_started is True
    assert user_id == await _user_id(factory, 4540)
    assert client.get("/auth/me", headers=_cookie_headers(token)).json() == {
        "user_id": user_id,
        "bot_started": True,
        "first_name": "Тест",
    }


@pytest.mark.asyncio
async def test_code_cannot_be_reused(factory, monkeypatch):
    code = await _login_command(monkeypatch, factory, 4550)
    client = TestClient(app)

    assert _verify(client, code).status_code == 200
    again = _verify(client, code)
    assert again.status_code == 400
    assert again.json() == {"detail": VERIFY_ERROR}


@pytest.mark.asyncio
async def test_expired_code_is_rejected(factory):
    async with factory() as s:
        code = await create_bot_login_code(s, 4560, ttl_seconds=-1)
    response = _verify(TestClient(app), code)
    assert response.status_code == 400
    assert response.json() == {"detail": VERIFY_ERROR}
    assert "set-cookie" not in response.headers


@pytest.mark.asyncio
async def test_wrong_code_is_rejected(factory, monkeypatch):
    code = await _login_command(monkeypatch, factory, 4570)
    wrong = "BBBB-BBBB" if code.replace("-", "") == "A" * 8 else "AAAA-AAAA"
    response = _verify(TestClient(app), wrong)
    assert response.status_code == 400
    assert response.json() == {"detail": VERIFY_ERROR}
    assert "set-cookie" not in response.headers


@pytest.mark.asyncio
async def test_empty_and_malformed_codes_are_400(factory):
    client = TestClient(app)
    for bad in ["", "   ", "-", "ABC", "ABCDEFGHJ", "ABCD-EFGI", "ABCD-EF0G", "абвг-абвг"]:
        response = _verify(client, bad)
        assert response.status_code == 400, bad
        assert response.json() == {"detail": VERIFY_ERROR}, bad


@pytest.mark.asyncio
async def test_overlong_code_is_400_same_as_wrong(factory, monkeypatch):
    """Код длиннее 32 символов (33 и 10000) даёт тот же ответ 400, что и неверный код, без cookie и без 422."""
    code = await _login_command(monkeypatch, factory, 4590)
    client = TestClient(app)
    for bad in [code + "A", "A" * 33, "A" * 10000]:
        response = _verify(client, bad)
        assert response.status_code == 400, len(bad)
        assert response.json() == {"detail": VERIFY_ERROR}, len(bad)
        assert "set-cookie" not in response.headers, len(bad)


@pytest.mark.asyncio
async def test_empty_code_field_is_400(factory):
    response = TestClient(app).post("/auth/bot-login/verify", json={"code": ""})
    assert response.status_code == 400
    assert response.json() == {"detail": VERIFY_ERROR}


@pytest.mark.asyncio
async def test_code_is_normalized_lowercase_without_dash(factory, monkeypatch):
    code = await _login_command(monkeypatch, factory, 4580)
    variant = "  " + code.lower().replace("-", "") + "  "
    assert _verify(TestClient(app), variant).status_code == 200


def test_old_bot_login_endpoints_are_removed(factory):
    client = TestClient(app)
    assert client.post("/auth/bot-login/start").status_code in (404, 405)
    assert client.get("/auth/bot-login/status", params={"code": "x"}).status_code in (404, 405)


def test_old_callback_handler_is_removed():
    assert not hasattr(handlers, "on_login_callback")
    assert not hasattr(handlers, "_login_keyboard")


# --- Команды бота ---------------------------------------------------------------------------


def test_login_is_in_bot_commands_and_help():
    assert "login" in [name for name, _ in BOT_COMMANDS]
    assert "/login" in HELP_TEXT


# --- Вход через Login Widget и Mini App (не меняется) ---------------------------------------


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


def test_me_ignores_bs_claim_in_token(factory):
    """Claim bs в токене не влияет на /auth/me: решает только БД. Пользователя 7 в БД нет."""
    token = make_session_token(7, bot_started=True)
    response = TestClient(app).get("/auth/me", headers=_cookie_headers(token))
    assert response.status_code == 200
    assert response.json() == {"user_id": 7, "bot_started": False, "first_name": None}


def test_me_without_session_is_401(factory):
    assert TestClient(app).get("/auth/me").status_code == 401


def test_token_without_bot_claim_reads_as_not_started():
    """Токены, выданные до появления поля bs, читаются как bot_started = False."""
    payload = base64.urlsafe_b64encode(json.dumps({"uid": 11, "exp": 4102444800}).encode()).decode()
    sig = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    assert read_session(f"{payload}.{sig}") == (11, False)
