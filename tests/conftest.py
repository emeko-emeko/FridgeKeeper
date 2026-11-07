"""Общие фикстуры тестов. Используется временная БД, а не instance/database.db."""

import pytest_asyncio

from core.database import init_db, make_session_factory


@pytest_asyncio.fixture
async def session(tmp_path):
    engine, factory = make_session_factory(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    await init_db(engine)
    async with factory() as s:
        yield s
    await engine.dispose()
