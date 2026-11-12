"""Точка входа бота. Запуск из корня проекта: python -m bot.main"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.handlers import router
from core.config import TELEGRAM_TOKEN
from core.scheduler import start_scheduler


async def main() -> None:
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Не задан TELEGRAM_TOKEN в файле .env")

    logging.basicConfig(level=logging.INFO)

    # Схему создаёт и меняет Alembic (alembic upgrade head), init_db здесь не нужен

    bot = Bot(TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    # Планировщик уведомлений работает в том же процессе, что и бот
    scheduler = start_scheduler(bot)
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
