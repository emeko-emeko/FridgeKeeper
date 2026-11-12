"""Тесты планировщика уведомлений на временной SQLite-базе с фейковым ботом."""

from datetime import date, datetime

import pytest
import pytest_asyncio
from sqlalchemy import select

from core.database import init_db, make_session_factory
from core.notifications import TZ, deadline_for
from core.scheduler import check_once, start_scheduler
from models import NotificationLog, Product, User

EXPIRY = date(2027, 5, 12)  # дедлайн: 13.05.2027 00:00


class FakeBot:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text):
        if self.fail:
            raise RuntimeError("telegram down")
        self.sent.append((chat_id, text))


@pytest_asyncio.fixture
async def factory(tmp_path):
    engine, factory = make_session_factory(f"sqlite+aiosqlite:///{tmp_path / 's.db'}")
    await init_db(engine)
    yield factory
    await engine.dispose()


async def _add_user_with_product(factory, telegram_id=555, expiry=EXPIRY):
    async with factory() as s:
        user = User(telegram_id=telegram_id)
        s.add(user)
        await s.flush()
        product = Product(user_id=user.id, name="Кефир", expiry_date=expiry)
        s.add(product)
        await s.commit()
        return product.id


async def _logs(factory, product_id):
    async with factory() as s:
        rows = (
            await s.execute(select(NotificationLog).where(NotificationLog.product_id == product_id))
        ).scalars().all()
        return sorted((r.level_hours, r.status) for r in rows)


@pytest.mark.asyncio
async def test_sends_once_at_due_level(factory):
    pid = await _add_user_with_product(factory)
    bot = FakeBot()
    now = datetime(2027, 5, 12, 12, 0, tzinfo=TZ)  # за 12 ч до дедлайна → уровень 12

    assert await check_once(bot, factory, now) == 1
    assert await check_once(bot, factory, now) == 0  # повторно не отправляет
    assert len(bot.sent) == 1
    assert bot.sent[0][0] == 555
    assert await _logs(factory, pid) == [(12, "sent"), (24, "skipped")]


@pytest.mark.asyncio
async def test_restart_sends_one_message_and_marks_skipped(factory):
    pid = await _add_user_with_product(factory)
    bot = FakeBot()
    now = datetime(2027, 5, 12, 23, 0, tzinfo=TZ)  # за 1 ч до дедлайна, ничего не отправлено

    assert await check_once(bot, factory, now) == 1
    assert len(bot.sent) == 1
    assert await _logs(factory, pid) == [(2, "sent"), (6, "skipped"), (12, "skipped"), (24, "skipped")]


@pytest.mark.asyncio
async def test_failed_send_is_retried_later(factory):
    pid = await _add_user_with_product(factory)
    now = datetime(2027, 5, 12, 12, 0, tzinfo=TZ)

    assert await check_once(FakeBot(fail=True), factory, now) == 0
    assert await _logs(factory, pid) == []

    bot = FakeBot()
    assert await check_once(bot, factory, now) == 1
    assert await _logs(factory, pid) == [(12, "sent"), (24, "skipped")]


@pytest.mark.asyncio
async def test_skips_product_without_telegram_or_date(factory):
    await _add_user_with_product(factory, telegram_id=None)
    await _add_user_with_product(factory, telegram_id=777, expiry=None)
    bot = FakeBot()
    now = datetime(2027, 5, 12, 23, 0, tzinfo=TZ)

    assert await check_once(bot, factory, now) == 0
    assert bot.sent == []


@pytest.mark.asyncio
async def test_nothing_after_deadline(factory):
    await _add_user_with_product(factory)
    bot = FakeBot()
    now = deadline_for(EXPIRY).replace(hour=1)  # уже после дедлайна

    assert await check_once(bot, factory, now) == 0
    assert bot.sent == []


@pytest.mark.asyncio
async def test_start_scheduler_registers_one_job_and_stops():
    scheduler = start_scheduler(FakeBot(), interval=3600)
    try:
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].trigger.interval.total_seconds() == 3600
    finally:
        scheduler.shutdown(wait=False)
