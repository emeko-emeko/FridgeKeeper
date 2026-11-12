"""Однократный перенос данных из SQLite в PostgreSQL.

Запуск (из корня проекта, DATABASE_URL уже указывает на PostgreSQL):
    uv run python -m scripts.migrate_sqlite_to_pg database.db
"""

import asyncio
import sqlite3
import sys
from datetime import date, datetime

from sqlalchemy import insert, text

from core.config import DATABASE_URL
from core.database import make_session_factory
from models import Product, User


def _dt(value):
    return datetime.fromisoformat(value) if value else None


def _date(value):
    return date.fromisoformat(value) if value else None


async def migrate(sqlite_path: str) -> None:
    src = sqlite3.connect(sqlite_path)
    src.row_factory = sqlite3.Row

    users = [
        {"id": r["id"], "telegram_id": r["telegram_id"], "created_at": _dt(r["created_at"])}
        for r in src.execute("SELECT * FROM users ORDER BY id")
    ]
    products = [
        {
            "id": r["id"],
            "user_id": r["user_id"],
            "name": r["name"],
            "category": r["category"],
            "expiry_date": _date(r["expiry_date"]),
            "expiry_source": None,  # в старой базе источника не было
            "storage_advice": r["storage_advice"],
            "created_at": _dt(r["created_at"]),
        }
        for r in src.execute("SELECT * FROM products ORDER BY id")
    ]
    src.close()

    engine, _ = make_session_factory(DATABASE_URL)
    async with engine.begin() as conn:
        # Порядок важен: сначала users, потом products (внешний ключ)
        if users:
            await conn.execute(insert(User), users)
        if products:
            await conn.execute(insert(Product), products)
        # Вставка с явными id не двигает автоинкремент PostgreSQL, поэтому выравниваем его
        for table in ("users", "products"):
            await conn.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
            ))
    await engine.dispose()
    print(f"Перенесено: пользователей {len(users)}, продуктов {len(products)}")
    async with engine.connect() as conn:
        existing = (await conn.execute(text("SELECT COUNT(*) FROM users"))).scalar_one()
    if existing:
        print(f"В PostgreSQL уже есть {existing} пользователей, перенос пропущен")
        await engine.dispose()
        return


if __name__ == "__main__":
    asyncio.run(migrate(sys.argv[1]))