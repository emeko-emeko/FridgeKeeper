"""Базовый класс ORM-моделей и вспомогательные функции."""

from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy-моделей проекта."""


def utcnow() -> datetime:
    """Текущее время в UTC без tzinfo (SQLite хранит наивные значения)."""
    return datetime.now(UTC).replace(tzinfo=None)
