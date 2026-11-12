"""Тесты эндпоинтов POST /products и GET /products на временной SQLite-базе."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from api.auth import SESSION_COOKIE, make_session_token
from api.products import get_session
from app import app
from core.database import init_db, make_session_factory
from models import User


@pytest_asyncio.fixture
async def factory(tmp_path):
    engine, factory = make_session_factory(f"sqlite+aiosqlite:///{tmp_path / 'api.db'}")
    await init_db(engine)
    async with factory() as s:
        s.add(User(id=1, telegram_id=None))
        await s.commit()

    async def override_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    yield factory
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
def client(factory):
    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, make_session_token(1))
    yield client


def test_list_requires_login():
    assert TestClient(app).get("/products").status_code == 401


def test_create_then_list(client):
    created = client.post(
        "/products", json={"name": "  Кефир  ", "expiry_date": "2027-05-12", "expiry_source": "ocr"}
    )
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Кефир"
    assert body["expiry_date"] == "2027-05-12"
    assert body["expiry_source"] == "ocr"

    items = client.get("/products").json()
    assert [(i["name"], i["expiry_date"]) for i in items] == [("Кефир", "2027-05-12")]


def test_create_without_date_defaults_to_manual(client):
    created = client.post("/products", json={"name": "Соль"})
    assert created.status_code == 201
    assert created.json()["expiry_date"] is None
    assert created.json()["expiry_source"] == "manual"


def test_create_rejects_empty_name(client):
    assert client.post("/products", json={"name": ""}).status_code == 422


def test_patch_name_and_date(client):
    pid = client.post("/products", json={"name": "Молоко"}).json()["id"]

    resp = client.patch(f"/products/{pid}", json={"name": "Молоко 3%", "expiry_date": "2027-06-01"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Молоко 3%"
    assert resp.json()["expiry_date"] == "2027-06-01"
    assert resp.json()["expiry_source"] == "manual"


def test_patch_clears_date_with_null(client):
    pid = client.post("/products", json={"name": "Соль", "expiry_date": "2027-06-01"}).json()["id"]

    resp = client.patch(f"/products/{pid}", json={"expiry_date": None})
    assert resp.json()["expiry_date"] is None


def test_patch_rejects_blank_name(client):
    pid = client.post("/products", json={"name": "Соль"}).json()["id"]
    assert client.patch(f"/products/{pid}", json={"name": "   "}).status_code == 422


def test_delete_removes_product(client):
    pid = client.post("/products", json={"name": "Кефир"}).json()["id"]

    assert client.delete(f"/products/{pid}").status_code == 204
    assert client.get("/products").json() == []


def test_other_users_product_is_not_found(client):
    pid = client.post("/products", json={"name": "Чужой"}).json()["id"]

    client.cookies.set(SESSION_COOKIE, make_session_token(2))
    assert client.patch(f"/products/{pid}", json={"name": "X"}).status_code == 404
    assert client.delete(f"/products/{pid}").status_code == 404
    client.cookies.set(SESSION_COOKIE, make_session_token(1))
