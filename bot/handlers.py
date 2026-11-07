"""Обработчики команд бота: /start, /help, /my_products."""

import html

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.filters.command import Command
from aiogram.types import Message

from bot.formatting import HELP_TEXT, LINK_MESSAGES, WELCOME_TEXT, format_products
from core.database import SessionFactory
from core.linking import LinkStatus, consume_link_token
from core.products import list_user_products
from core.users import get_or_create_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    """Регистрирует пользователя; при /start <token> связывает аккаунт с сайтом."""
    telegram_id = message.from_user.id

    async with SessionFactory() as session:
        # Сначала связывание: иначе запись, созданная get_or_create_user, сама займёт telegram_id
        if command.args:
            status = await consume_link_token(session, command.args.strip(), telegram_id)
            await get_or_create_user(session, telegram_id)
            await message.answer(LINK_MESSAGES[status.value])
            return

        await get_or_create_user(session, telegram_id)

    name = html.escape(message.from_user.first_name or "друг")
    await message.answer(WELCOME_TEXT.format(name=name))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Список команд и описание сервиса."""
    await message.answer(HELP_TEXT)


@router.message(Command("my_products"))
async def cmd_my_products(message: Message) -> None:
    """Продукты текущего пользователя с датами окончания срока годности."""
    telegram_id = message.from_user.id

    async with SessionFactory() as session:
        user = await get_or_create_user(session, telegram_id)
        products = await list_user_products(session, user.id)

    await message.answer(format_products(products))
