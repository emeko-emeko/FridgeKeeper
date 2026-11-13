"""Текст сообщений бота. Чистые функции без обращения к Telegram и БД, легко тестируются."""

import html
import math
from collections.abc import Sequence
from datetime import datetime, timedelta

from core.notifications import TZ, deadline_for
from models import Product

HELP_TEXT = (
    "<b>FridgeKeeper</b> следит за сроками годности продуктов.\n\n"
    "<b>Команды:</b>\n"
    "/start — регистрация и приветствие\n"
    "/help — это сообщение\n"
    "/my_products — список ваших продуктов и сроки их годности\n"
    "/add — добавить продукт: <code>/add Название; ДД.ММ.ГГГГ</code> (дату можно не указывать)\n"
    "/soon — что истекает в ближайшие 3 дня\n"
    "/delete — удалить продукт: <code>/delete Название</code>\n\n"
    "<b>Фото:</b> пришлите фото этикетки, бот найдёт название и дату и попросит подтвердить.\n\n"
    "<b>Связывание с сайтом:</b>\n"
    "Откройте ссылку, которую выдал сайт, — бот привяжет ваш Telegram "
    "к веб-аккаунту. Ссылка действует ограниченное время и работает один раз."
)

WELCOME_TEXT = (
    "Привет, {name}! Я бот <b>FridgeKeeper</b>.\n\n"
    "Я помогу не пропустить срок годности продуктов.\n"
    "Команда /help покажет список команд."
)

PHOTO_TEXTS = {
    "proposal": "Нашёл: <b>{name}</b>, годен до {expiry}. Сохранить?",
    "guess_note": "\n<i>Дата без подписи «годен до», взята как предположение. Проверьте её.</i>",
    "expired_warning": "⚠️ Срок на этикетке уже истёк. Сохранить можно, но проверьте продукт.",
    "ask_name": "Дату нашёл ({expiry}), но название не распознал. Напишите название продукта текстом.",
    "ask_name_again": "Название должно быть от 1 до 100 символов. Напишите его ещё раз.",
    "ask_manual": "Введите продукт вручную: <code>Название; ДД.ММ.ГГГГ</code> (дату можно не указывать).",
    "saved": "Сохранено: {name}. {left}",
    "ocr_failed": "Не удалось распознать фото. Попробуйте ещё раз или добавьте вручную: /add Название; ДД.ММ.ГГГГ",
    "delete_ambiguous": "Найдено продуктов с таким названием: {count}. Удалите лишние на сайте, там их видно по дате.",
}

LINK_MESSAGES = {
    "ok": "Аккаунт успешно связан с сайтом. Теперь ваши продукты доступны здесь.",
    "invalid": "Ссылка связывания недействительна. Запросите новую на сайте.",
    "expired": "Срок действия ссылки истёк. Запросите новую на сайте.",
    "used": "Эта ссылка уже использована. Запросите новую на сайте.",
    "already_linked": (
        "Не удалось связать аккаунт: этот Telegram или аккаунт сайта уже привязан "
        "к другому пользователю."
    ),
}


def format_products(products: Sequence[Product], now: datetime | None = None) -> str:
    """Список продуктов: дата окончания срока и сколько осталось."""
    if not products:
        return "У вас пока нет продуктов. Добавьте их на сайте."

    now = now or datetime.now(TZ)
    lines = ["<b>Ваши продукты:</b>"]
    for product in products:
        # Название пользователя экранируем: Telegram разбирает HTML-разметку
        name = html.escape(product.name)
        if product.expiry_date is None:
            lines.append(f"• {name} — срок не указан")
            continue
        expiry = product.expiry_date.strftime("%d.%m.%Y")
        left = time_left_text(product.expiry_date, now)
        lines.append(f"• {name} — до {expiry}, {left}")
    return "\n".join(lines)


def time_left_text(expiry, now: datetime) -> str:
    """Меньше 24 часов до конца срока — часы («осталось 5 ч»), иначе дни."""
    if expiry is None:
        return "срок не указан"
    remaining = deadline_for(expiry) - now
    if timedelta(0) < remaining < timedelta(hours=24):
        hours = max(1, math.floor(remaining.total_seconds() / 3600))
        return f"осталось {hours} ч"
    return days_left_text(expiry, now.date())


# Меню команд в Telegram: появляется, когда пользователь набирает «/»
BOT_COMMANDS: list[tuple[str, str]] = [
    ("start", "Регистрация и приветствие"),
    ("help", "Список команд и как пользоваться"),
    ("my_products", "Мои продукты и сроки годности"),
    ("add", "Добавить продукт: /add Название; ДД.ММ.ГГГГ"),
    ("soon", "Что истекает в ближайшие 3 дня"),
    ("delete", "Удалить продукт: /delete Название"),
]


def _days_word(n: int) -> str:
    """Склонение слова «день» после числа: 1 день, 2 дня, 5 дней."""
    if n % 100 in (11, 12, 13, 14):
        return "дней"
    if n % 10 == 1:
        return "день"
    if n % 10 in (2, 3, 4):
        return "дня"
    return "дней"


def days_left_text(expiry, today) -> str:
    """Сколько осталось до срока: «осталось 5 дней», «истекает сегодня», «истёк 2 дня назад»."""
    if expiry is None:
        return "срок не указан"
    delta = (expiry - today).days
    if delta < 0:
        n = -delta
        return f"срок истёк {n} {_days_word(n)} назад"
    if delta == 0:
        return "истекает сегодня"
    return f"осталось {delta} {_days_word(delta)}"
