"""Тесты регистрации пользователей и связывания токеном."""

import pytest

from core.linking import LinkStatus, consume_link_token, create_link_token
from core.users import create_web_user, get_or_create_user


@pytest.mark.asyncio
async def test_get_or_create_user_is_idempotent(session):
    first = await get_or_create_user(session, 111)
    second = await get_or_create_user(session, 111)
    assert first.id == second.id
    assert second.telegram_id == 111


@pytest.mark.asyncio
async def test_valid_token_links_telegram_id(session):
    web_user = await create_web_user(session)
    assert web_user.telegram_id is None

    token = await create_link_token(session, web_user.id)
    status = await consume_link_token(session, token, telegram_id=222)

    assert status is LinkStatus.OK
    await session.refresh(web_user)
    assert web_user.telegram_id == 222


@pytest.mark.asyncio
async def test_token_is_one_time(session):
    web_user = await create_web_user(session)

    token = await create_link_token(session, web_user.id)
    assert await consume_link_token(session, token, telegram_id=333) is LinkStatus.OK
    assert await consume_link_token(session, token, telegram_id=333) is LinkStatus.USED


@pytest.mark.asyncio
async def test_expired_token_is_rejected(session):
    web_user = await create_web_user(session)

    token = await create_link_token(session, web_user.id, ttl_minutes=-1)
    assert await consume_link_token(session, token, telegram_id=444) is LinkStatus.EXPIRED


@pytest.mark.asyncio
async def test_unknown_token_is_invalid(session):
    assert await consume_link_token(session, "no-such-token", telegram_id=555) is LinkStatus.INVALID


@pytest.mark.asyncio
async def test_telegram_id_already_taken_is_conflict(session):
    # Telegram 666 уже привязан к другому аккаунту
    await get_or_create_user(session, 666)

    web_user = await create_web_user(session)
    token = await create_link_token(session, web_user.id)
    assert await consume_link_token(session, token, telegram_id=666) is LinkStatus.ALREADY_LINKED
