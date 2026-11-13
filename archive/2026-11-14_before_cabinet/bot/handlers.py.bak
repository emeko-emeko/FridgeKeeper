"""Обработчики бота: команды, фото этикетки и подтверждение добавления."""

import html
import io
from datetime import date, datetime

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart, StateFilter
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.formatting import (
    HELP_TEXT,
    LINK_MESSAGES,
    LOGIN_CODE_TEXT,
    PHOTO_TEXTS,
    WELCOME_TEXT,
    days_left_text,
    format_products,
)
from core.bot_login import create_bot_login_code
from core.database import SessionFactory
from core.label_service import analyze_label
from core.linking import LinkStatus, consume_link_token
from core.notifications import TZ
from core.ocr import OcrError
from core.products import find_products_by_name, list_user_products, products_expiring_within
from core.users import get_or_create_user, mark_bot_started
from models import Product

router = Router()

LOGIN_START_ARG = "login"  # /start login: та же выдача кода, что и команда /login


class AddFromPhoto(StatesGroup):
    confirm = State()    # ждём «Да, сохранить» / «Нет, введу сам»
    manual = State()     # ждём «Название; ДД.ММ.ГГГГ»
    name_only = State()  # на фото нет названия, ждём его текстом

ADD_USAGE = "Формат: <code>/add Название; ДД.ММ.ГГГГ</code> (дату можно не указывать)"


def parse_add_args(text: str) -> tuple[str, date | None] | None:
    """Разбирает «Название; ДД.ММ.ГГГГ». Возвращает None, если формат неверный."""
    name, sep, raw_date = text.partition(";")
    name = name.strip()
    if not name or len(name) > 100:
        return None
    if not sep or not raw_date.strip():
        return name, None
    try:
        return name, datetime.strptime(raw_date.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


async def _send_login_code(message: Message, telegram_id: int) -> None:
    """Выдаёт код входа этому пользователю. Код уходит только в его чат с ботом."""
    async with SessionFactory() as session:
        await mark_bot_started(session, telegram_id)
        code = await create_bot_login_code(session, telegram_id)
    await message.answer(LOGIN_CODE_TEXT.format(code=code))


@router.message(Command("login"))
async def cmd_login(message: Message) -> None:
    """Код для входа на сайт, привязанный к тому, кто написал команду."""
    await _send_login_code(message, message.from_user.id)


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    """Регистрирует пользователя; /start login выдаёт код входа; /start <token> связывает аккаунт."""
    telegram_id = message.from_user.id

    if (command.args or "").strip() == LOGIN_START_ARG:
        await _send_login_code(message, telegram_id)
        return

    async with SessionFactory() as session:
        # Сначала связывание: иначе запись, созданная get_or_create_user, сама займёт telegram_id
        if command.args:
            status = await consume_link_token(session, command.args.strip(), telegram_id)
            await mark_bot_started(session, telegram_id)
            await message.answer(LINK_MESSAGES[status.value])
            return

        await mark_bot_started(session, telegram_id)

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


@router.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject) -> None:
    """Добавляет продукт, введённый текстом. Срок необязателен."""
    parsed = parse_add_args(command.args or "")
    if parsed is None:
        await message.answer(ADD_USAGE)
        return
    name, expiry = parsed

    async with SessionFactory() as session:
        user = await get_or_create_user(session, message.from_user.id)
        session.add(Product(user_id=user.id, name=name, expiry_date=expiry, expiry_source="bot"))
        await session.commit()

    date_text = expiry.strftime("%d.%m.%Y") if expiry else "не указан"
    left = days_left_text(expiry, datetime.now(TZ).date())
    await message.answer(f"Добавлено: {html.escape(name)}, срок: {date_text}. {left}")


async def _save_product(telegram_id: int, name: str, expiry: date | None, source: str) -> None:
    async with SessionFactory() as session:
        user = await get_or_create_user(session, telegram_id)
        session.add(Product(user_id=user.id, name=name, expiry_date=expiry, expiry_source=source))
        await session.commit()


def _fmt(d: date | None) -> str:
    return d.strftime("%d.%m.%Y") if d else "не найден"


def _confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, сохранить", callback_data="photo:yes"),
                InlineKeyboardButton(text="Нет, введу сам", callback_data="photo:no"),
            ]
        ]
    )


@router.message(Command("soon"))
async def cmd_soon(message: Message) -> None:
    """Продукты, у которых срок истекает в ближайшие 3 дня, включая просроченные."""
    today = datetime.now(TZ).date()
    async with SessionFactory() as session:
        user = await get_or_create_user(session, message.from_user.id)
        products = await products_expiring_within(session, user.id, today, days=3)

    if not products:
        await message.answer("В ближайшие 3 дня ничего не истекает.")
        return
    lines = ["<b>Скоро испортится:</b>"]
    for p in products:
        status = "просрочен" if p.expiry_date < today else f"до {p.expiry_date.strftime('%d.%m.%Y')}"
        lines.append(f"• {html.escape(p.name)} — {status}")
    await message.answer("\n".join(lines))


@router.message(Command("delete"))
async def cmd_delete(message: Message, command: CommandObject) -> None:
    """Удаляет продукт по названию. Если совпадений несколько, ничего не удаляет."""
    name = (command.args or "").strip()
    if not name:
        await message.answer("Формат: <code>/delete Название</code>")
        return

    async with SessionFactory() as session:
        user = await get_or_create_user(session, message.from_user.id)
        matches = await find_products_by_name(session, user.id, name)
        if not matches:
            await message.answer(f"Продукт «{html.escape(name)}» не найден.")
            return
        if len(matches) > 1:
            await message.answer(PHOTO_TEXTS["delete_ambiguous"].format(count=len(matches)))
            return
        await session.delete(matches[0])
        await session.commit()
    await message.answer(f"Удалено: {html.escape(name)}")


@router.message(F.photo)
async def on_photo(message: Message, state: FSMContext) -> None:
    """Фото этикетки: распознаём, показываем название и дату, просим подтвердить."""
    buffer = io.BytesIO()
    photo = message.photo[-1]  # самое большое разрешение
    file = await message.bot.get_file(photo.file_id)
    await message.bot.download_file(file.file_path, destination=buffer)

    try:
        result = await analyze_label(buffer.getvalue())
    except OcrError:
        await message.answer(PHOTO_TEXTS["ocr_failed"])
        return

    today = datetime.now(TZ).date()
    await state.update_data(
        expiry=result.expiry_date.isoformat() if result.expiry_date else None,
    )

    if result.expiry_date and result.expiry_date < today:
        await message.answer(PHOTO_TEXTS["expired_warning"])

    if not result.product_name:
        await state.set_state(AddFromPhoto.name_only)
        await message.answer(PHOTO_TEXTS["ask_name"].format(expiry=_fmt(result.expiry_date)))
        return

    await state.update_data(name=result.product_name)
    await state.set_state(AddFromPhoto.confirm)
    guess_note = PHOTO_TEXTS["guess_note"] if result.confidence == "guess" else ""
    await message.answer(
        PHOTO_TEXTS["proposal"].format(
            name=html.escape(result.product_name), expiry=_fmt(result.expiry_date)
        )
        + guess_note,
        reply_markup=_confirm_keyboard(),
    )


@router.callback_query(StateFilter(AddFromPhoto.confirm), F.data == "photo:yes")
async def on_photo_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    expiry = date.fromisoformat(data["expiry"]) if data.get("expiry") else None
    await _save_product(callback.from_user.id, data["name"], expiry, "ocr")
    await state.clear()
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    left = days_left_text(expiry, datetime.now(TZ).date())
    await callback.message.answer(PHOTO_TEXTS["saved"].format(name=html.escape(data["name"]), left=left))


@router.callback_query(StateFilter(AddFromPhoto.confirm), F.data == "photo:no")
async def on_photo_reject(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddFromPhoto.manual)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(PHOTO_TEXTS["ask_manual"])


@router.message(StateFilter(AddFromPhoto.manual), F.text, ~F.text.startswith("/"))
async def on_manual_text(message: Message, state: FSMContext) -> None:
    parsed = parse_add_args(message.text)
    if parsed is None:
        await message.answer(ADD_USAGE)
        return
    name, expiry = parsed
    await _save_product(message.from_user.id, name, expiry, "manual")
    await state.clear()
    left = days_left_text(expiry, datetime.now(TZ).date())
    await message.answer(
        f"Добавлено: {html.escape(name)}, срок: {_fmt(expiry) if expiry else 'не указан'}. {left}"
    )


@router.message(StateFilter(AddFromPhoto.name_only), F.text, ~F.text.startswith("/"))
async def on_name_text(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name or len(name) > 100:
        await message.answer(PHOTO_TEXTS["ask_name_again"])
        return
    data = await state.get_data()
    expiry = date.fromisoformat(data["expiry"]) if data.get("expiry") else None
    await _save_product(message.from_user.id, name, expiry, "ocr" if expiry else "manual")
    await state.clear()
    left = days_left_text(expiry, datetime.now(TZ).date())
    await message.answer(PHOTO_TEXTS["saved"].format(name=html.escape(name), left=left))
