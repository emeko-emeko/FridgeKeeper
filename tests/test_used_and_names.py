"""Тесты: отметка «Использовано», имя пользователя (first_name), маршрут /cabinet и миграция 0004.

Работают на временной SQLite, база FridgeKeeper не трогается. Миграция не применяется, проверяется только цепочка.
"""

import hashlib
import hmac
import json
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import select

import core.telegram_auth as tg_auth
from api.auth import SESSION_COOKIE, get_session, make_session_token
from api.products import get_session as products_get_session
from app import app
from core.database import init_db, make_session_factory
from core.notifications import TZ
from core.products import list_user_products, products_expiring_within
from core.scheduler import check_once
from core.users import get_or_create_user, normalize_first_name
from models import Product, User

ROOT = Path(__file__).resolve().parent.parent
TOKEN = "123456:TEST_TOKEN"


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text):
        self.sent.append((chat_id, text))


@pytest_asyncio.fixture
async def factory(tmp_path):
    engine, factory = make_session_factory(f"sqlite+aiosqlite:///{tmp_path / 'used.db'}")
    await init_db(engine)
    async with factory() as s:
        s.add(User(id=1, telegram_id=None))
        s.add(User(id=2, telegram_id=None))
        await s.commit()

    async def override_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[products_get_session] = override_session
    yield factory
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
def client(factory):
    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, make_session_token(1))
    yield client


def _create(client, name="Кефир", expiry="2027-05-12"):
    body = {"name": name}
    if expiry:
        body["expiry_date"] = expiry
    resp = client.post("/products", json=body)
    assert resp.status_code == 201
    return resp.json()["id"]


# --- отметка «Использовано» ---------------------------------------------------------------

def test_new_product_has_used_at_null(client):
    created = client.post("/products", json={"name": "Соль"}).json()
    assert created["used_at"] is None
    assert client.get("/products").json()[0]["used_at"] is None


def test_patch_used_true_sets_time(client):
    pid = _create(client)
    resp = client.patch(f"/products/{pid}", json={"used": True})
    assert resp.status_code == 200
    used_at = resp.json()["used_at"]
    assert isinstance(used_at, str)
    datetime.fromisoformat(used_at)  # формат ISO


def test_patch_used_true_keeps_existing_time(client):
    pid = _create(client)
    first = client.patch(f"/products/{pid}", json={"used": True}).json()["used_at"]
    second = client.patch(f"/products/{pid}", json={"used": True}).json()["used_at"]
    # SQLite отдаёт время без часового пояса, PostgreSQL — с ним; сравниваем без пояса
    assert datetime.fromisoformat(first).replace(tzinfo=None) == datetime.fromisoformat(second).replace(tzinfo=None)


def test_patch_used_false_clears_time(client):
    pid = _create(client)
    client.patch(f"/products/{pid}", json={"used": True})
    resp = client.patch(f"/products/{pid}", json={"used": False})
    assert resp.json()["used_at"] is None
    assert client.get("/products").json()[0]["used_at"] is None


def test_patch_used_keeps_name_and_date(client):
    pid = _create(client, name="Йогурт", expiry="2027-05-12")
    resp = client.patch(f"/products/{pid}", json={"used": True})
    assert resp.json()["name"] == "Йогурт"
    assert resp.json()["expiry_date"] == "2027-05-12"


def test_patch_used_on_other_users_product_is_404(client):
    pid = _create(client)
    client.cookies.set(SESSION_COOKIE, make_session_token(2))
    assert client.patch(f"/products/{pid}", json={"used": True}).status_code == 404
    client.cookies.set(SESSION_COOKIE, make_session_token(1))


def test_get_list_contains_used_at(client):
    pid = _create(client)
    client.patch(f"/products/{pid}", json={"used": True})
    items = client.get("/products").json()
    assert items[0]["id"] == pid
    assert isinstance(items[0]["used_at"], str)


@pytest.mark.asyncio
async def test_used_product_is_excluded_from_soon(session):
    user = await get_or_create_user(session, 911)
    today = date(2026, 11, 13)
    session.add_all([
        Product(user_id=user.id, name="Активный", expiry_date=date(2026, 11, 14)),
        Product(
            user_id=user.id,
            name="Использован",
            expiry_date=date(2026, 11, 14),
            used_at=datetime(2026, 11, 13, 10, 0),
        ),
    ])
    await session.commit()

    rows = await products_expiring_within(session, user.id, today, days=3)
    assert [p.name for p in rows] == ["Активный"]


@pytest.mark.asyncio
async def test_list_can_hide_used_products(session):
    user = await get_or_create_user(session, 912)
    session.add_all([
        Product(user_id=user.id, name="Активный", expiry_date=date(2027, 1, 1)),
        Product(user_id=user.id, name="Использован", expiry_date=date(2027, 1, 2), used_at=datetime(2026, 11, 1)),
    ])
    await session.commit()

    all_rows = await list_user_products(session, user.id)
    active = await list_user_products(session, user.id, include_used=False)
    assert [p.name for p in all_rows] == ["Активный", "Использован"]
    assert [p.name for p in active] == ["Активный"]


@pytest.mark.asyncio
async def test_scheduler_skips_used_products(tmp_path):
    engine, factory = make_session_factory(f"sqlite+aiosqlite:///{tmp_path / 'sched.db'}")
    await init_db(engine)
    try:
        async with factory() as s:
            user = User(telegram_id=7001)
            s.add(user)
            await s.flush()
            s.add(Product(user_id=user.id, name="Использован", expiry_date=date(2027, 5, 12),
                          used_at=datetime(2027, 5, 11)))
            await s.commit()

        bot = FakeBot()
        now = datetime(2027, 5, 12, 12, 0, tzinfo=TZ)  # уровень 12 ч, но продукт использован
        assert await check_once(bot, factory, now) == 0
        assert bot.sent == []
        async with factory() as s:
            from models import NotificationLog
            logs = (await s.execute(select(NotificationLog))).scalars().all()
            assert logs == []
    finally:
        await engine.dispose()


# --- first_name -----------------------------------------------------------------------------

def test_normalize_first_name_trims_and_limits():
    assert normalize_first_name("  Айгуль  ") == "Айгуль"
    assert normalize_first_name("") is None
    assert normalize_first_name("   ") is None
    assert normalize_first_name(None) is None
    assert len(normalize_first_name("я" * 100)) == 64


@pytest.mark.asyncio
async def test_first_name_saved_on_create_and_updated_on_change(session):
    user = await get_or_create_user(session, 921, first_name="Айгуль")
    assert user.first_name == "Айгуль"

    user = await get_or_create_user(session, 921, first_name="Айжан")
    assert user.first_name == "Айжан"


@pytest.mark.asyncio
async def test_empty_first_name_does_not_erase_saved_one(session):
    await get_or_create_user(session, 922, first_name="Марат")
    user = await get_or_create_user(session, 922, first_name=None)
    assert user.first_name == "Марат"


@pytest.mark.asyncio
async def test_long_first_name_is_cut_to_64(session):
    user = await get_or_create_user(session, 923, first_name="а" * 200)
    assert len(user.first_name) == 64


@pytest.mark.asyncio
async def test_auth_me_returns_first_name(factory):
    async with factory() as s:
        s.add(User(id=5, telegram_id=5005, first_name="Нурлан"))
        await s.commit()

    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, make_session_token(5))
    assert client.get("/auth/me").json()["first_name"] == "Нурлан"


def test_auth_me_first_name_null_when_unknown(client):
    assert client.get("/auth/me").json()["first_name"] is None


def _sign_mini_app(fields: dict) -> str:
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


@pytest.mark.asyncio
async def test_mini_app_login_saves_first_name(factory, monkeypatch):
    monkeypatch.setattr(tg_auth, "TELEGRAM_TOKEN", TOKEN)
    user = json.dumps({"id": 6006, "first_name": "Диас"}, ensure_ascii=False)
    init_data = _sign_mini_app({"auth_date": str(int(time.time())), "user": user})

    client = TestClient(app)
    assert client.post("/auth/mini-app", json={"init_data": init_data}).status_code == 200

    async with factory() as s:
        assert (await s.scalar(select(User).where(User.telegram_id == 6006))).first_name == "Диас"


def test_mini_app_first_name_helper_is_safe_on_garbage():
    assert tg_auth.mini_app_first_name("x") is None
    assert tg_auth.mini_app_first_name("user=%7Bbroken") is None


def test_login_widget_passes_first_name_field(monkeypatch):
    """Имя из виджета уходит в get_or_create_user; подпись проверяется как раньше."""
    import api.auth as auth_module

    monkeypatch.setattr(tg_auth, "TELEGRAM_TOKEN", TOKEN)
    fields = {"id": "7007", "first_name": "Камила", "auth_date": str(int(time.time()))}
    secret = hashlib.sha256(TOKEN.encode()).digest()
    fields["hash"] = hmac.new(secret, tg_auth._check_string(fields).encode(), hashlib.sha256).hexdigest()
    seen = {}

    class FakeUser:
        id = 9

    async def fake(session, telegram_id, first_name=None):
        seen["name"] = first_name
        return FakeUser()

    monkeypatch.setattr(auth_module, "get_or_create_user", fake)
    response = TestClient(app).get(f"/auth/login-widget?{urlencode(fields)}", follow_redirects=False)
    assert response.status_code == 303
    assert seen["name"] == fields["first_name"]


# --- /cabinet -------------------------------------------------------------------------------

def test_cabinet_without_login_redirects_to_login():
    response = TestClient(app).get("/cabinet", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


# --- миграция 0004 ----------------------------------------------------------------------------

def test_migration_0004_is_the_single_head_after_0003():
    cfg = Config()
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == ["0004"]
    assert script.get_revision("0004").down_revision == "0003"
