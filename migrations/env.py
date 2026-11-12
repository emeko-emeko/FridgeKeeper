"""Окружение Alembic: подключение к БД и метаданные моделей."""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

# Корень проекта (папка выше migrations/), чтобы работали импорты core и models
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alembic import context  # noqa: E402
from sqlalchemy import pool  # noqa: E402
from sqlalchemy.engine import Connection  # noqa: E402
from sqlalchemy.ext.asyncio import async_engine_from_config  # noqa: E402

from core.config import DATABASE_URL  # noqa: E402
from models import Base  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", DATABASE_URL)
target_metadata = Base.metadata

# дальше без изменений: run_migrations_offline, do_run_migrations,
# run_async_migrations, run_migrations_online и вызов в конце файла


def run_migrations_offline() -> None:
    """Режим без подключения: генерирует SQL в файл."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()