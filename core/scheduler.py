"""Планировщик уведомлений о сроке годности.

Раз в CHECK_INTERVAL_SECONDS проверяет продукты с датой и привязанным Telegram,
решает по core.notifications.decide, что отправить, и пишет результат в notification_log.
Запускается из bot/main.py в том же процессе, что и бот.
"""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.database import SessionFactory
from core.notifications import TZ, build_message, decide, deadline_for
from models import NotificationLog, Product, User

log = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 300  # проверка каждые 5 минут


async def check_once(
    bot,
    factory: async_sessionmaker[AsyncSession],
    now: datetime | None = None,
) -> int:
    """Одна проверка всех продуктов. Возвращает число отправленных сообщений."""
    now = now or datetime.now(TZ)
    sent = 0

    async with factory() as session:
        rows = (
            await session.execute(
                select(Product, User.telegram_id)
                .join(User, Product.user_id == User.id)
                .where(Product.expiry_date.is_not(None), User.telegram_id.is_not(None))
            )
        ).all()

        for product, telegram_id in rows:
            deadline = deadline_for(product.expiry_date)
            logged = (
                await session.execute(
                    select(NotificationLog).where(NotificationLog.product_id == product.id)
                )
            ).scalars().all()
            handled = {row.level_hours for row in logged}

            decision = decide(deadline, now, handled)
            if decision.send_level is None and not decision.skip_levels:
                continue

            if decision.send_level is not None:
                text = build_message(product.name, deadline, now)
                try:
                    await bot.send_message(telegram_id, text)
                except Exception:
                    # Уровень не записываем: попробуем снова на следующей проверке
                    log.exception("Не удалось отправить уведомление по продукту %s", product.id)
                    continue
                session.add(
                    NotificationLog(
                        product_id=product.id,
                        level_hours=decision.send_level,
                        status="sent",
                    )
                )
                sent += 1

            for level in decision.skip_levels:
                session.add(
                    NotificationLog(product_id=product.id, level_hours=level, status="skipped")
                )

            await session.commit()

    return sent


async def _job(bot) -> None:
    """Задача APScheduler. Ошибка одной проверки не останавливает расписание."""
    try:
        sent = await check_once(bot, SessionFactory)
        if sent:
            log.info("Отправлено уведомлений: %s", sent)
    except Exception:
        log.exception("Ошибка проверки сроков годности")


def start_scheduler(bot, interval: int = CHECK_INTERVAL_SECONDS) -> AsyncIOScheduler:
    """Запускает APScheduler в текущем event loop. Останавливать через scheduler.shutdown()."""
    scheduler = AsyncIOScheduler(timezone=TZ)
    scheduler.add_job(_job, "interval", seconds=interval, args=[bot], max_instances=1)
    scheduler.start()
    return scheduler
