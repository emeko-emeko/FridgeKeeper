"""Подключение к базе данных (асинхронный SQLAlchemy поверх SQLite)."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import DATABASE_URL
from models import Base


def make_session_factory(url: str) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Создаёт движок и фабрику сессий для указанной строки подключения."""
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, factory


# Общие движок и фабрика сессий приложения
engine, SessionFactory = make_session_factory(DATABASE_URL)


async def init_db(target_engine: AsyncEngine = engine) -> None:
    """Создаёт недостающие таблицы. Уже существующие таблицы не изменяются."""
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
