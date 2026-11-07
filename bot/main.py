"""Точка входа бота. Запуск из корня проекта: python -m bot.main"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.handlers import router
from core.config import TELEGRAM_TOKEN
from core.database import init_db


async def main() -> None:
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Не задан TELEGRAM_TOKEN в файле .env")

    logging.basicConfig(level=logging.INFO)

    # Создаёт недостающие таблицы (users и products уже есть в базе)
    await init_db()

    bot = Bot(TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
