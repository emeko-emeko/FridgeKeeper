"""Модель пользователя. Схема совпадает с таблицей users из instance/create_db.py."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Telegram ID. NULL, пока аккаунт создан на сайте и ещё не связан с ботом.
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    # Первый /start в боте (или подтверждение входа кнопкой). NULL, пока бота не открывали.
    bot_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    products: Mapped[list["Product"]] = relationship(  # noqa: F821 (определена в product.py)
        back_populates="user", cascade="all, delete-orphan"
    )
