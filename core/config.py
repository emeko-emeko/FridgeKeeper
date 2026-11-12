"""Настройки приложения. Значения берутся из переменных окружения и файла .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Корень проекта (папка, где лежит app.py)
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

# Токен Telegram-бота (получить у @BotFather)
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
# Yandex Vision (распознавание текста на этикетке)
YANDEX_API_KEY: str = os.getenv("YANDEX_API_KEY", "")
YANDEX_FOLDER_ID: str = os.getenv("YANDEX_FOLDER_ID", "")

# Строка подключения SQLAlchemy (асинхронный драйвер aiosqlite)
DATABASE_URL_RAW: str = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{(BASE_DIR / 'instance' / 'database.db').as_posix()}",
)

# Neon и Vercel выдают postgres:// или postgresql://, SQLAlchemy нужен драйвер asyncpg
DATABASE_URL: str = DATABASE_URL_RAW.replace("postgres://", "postgresql+asyncpg://", 1).replace(
    "postgresql://", "postgresql+asyncpg://", 1
) if DATABASE_URL_RAW.startswith(("postgres://", "postgresql://")) else DATABASE_URL_RAW

# Срок жизни токена связки с Telegram, в минутах
LINK_TOKEN_TTL_MINUTES: int = int(os.getenv("LINK_TOKEN_TTL_MINUTES", "10"))

# Ключ подписи сессий. На Vercel обязателен одинаковый для всех инстансов.
# Если не задан, на каждом запуске генерируется случайный (сессии слетают при перезапуске).
SESSION_SECRET: str = os.getenv("SESSION_SECRET", "") or __import__("secrets").token_hex(32)
