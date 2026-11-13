"""Одноразовый код входа на сайт через бота (вариант «войти через бота»).

В БД хранится только SHA-256 хэш кода, сам код выдаётся браузеру один раз.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, utcnow


class LoginCode(Base):
    __tablename__ = "login_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Заполняется, когда бот подтвердил вход (/start login_<code>)
    confirmed_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Заполняется, когда сайт забрал cookie: код больше не работает
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
