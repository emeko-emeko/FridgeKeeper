"""Общие фикстуры тестов. Используется временная БД, а не instance/database.db."""

import os

import pytest_asyncio
from dotenv import load_dotenv

# Строка подключения к тестовой БД лежит в .env (TEST_DATABASE_URL), а не в коде
load_dotenv()
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL") or "sqlite+aiosqlite:///:memory:"

from core.database import init_db, make_session_factory  # noqa: E402


@pytest_asyncio.fixture
async def session(tmp_path):
    engine, factory = make_session_factory(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    await init_db(engine)
    async with factory() as s:
        yield s
    await engine.dispose()
