"""Тексты лендинга на русском и английском языках."""

from __future__ import annotations

SUPPORTED_LANGS: tuple[str, ...] = ("ru", "en")
DEFAULT_LANG = "ru"

TELEGRAM_BOT_URL = "https://t.me/FridgeKeeper_MESSAGE_BOT"
APP_URL = "/app"

TEXTS: dict[str, dict[str, str]] = {
    "ru": {
        "html_lang": "ru",
        "page_title": "FridgeKeeper — контроль сроков годности",
        "meta_description": "FridgeKeeper помнит, что лежит в холодильнике, и напоминает до того, как продукт испортится.",
        "brand": "FridgeKeeper",
        "lang_switch": "English",
        "nav_open": "Открыть продукт",
        "hero_eyebrow": "Food Waste at Home",
        "hero_title_pre": "Контролируйте",
        "hero_title_hl": "сроки годности",
        "hero_title_post": "и не выбрасывайте еду",
        "hero_sub": "FridgeKeeper помнит, что лежит в холодильнике, и напоминает до того, как продукт испортится. Добавляйте товары по фото этикетки или вручную.",
        "cta_primary": "Открыть FridgeKeeper",
        "cta_secondary": "Подключить Telegram",
        "problems_eyebrow": "Проблема",
        "problems_title": "Почему еда портится дома",
        "problem1_title": "Слепые зоны холодильника",
        "problem1_text": "Покупаем то, что уже есть, потому что забыли о продукте на задней полке.",
        "problem2_title": "Нет контроля сроков",
        "problem2_text": "Даты на упаковках легко пропустить, а автоматических напоминаний обычно нет.",
        "problem3_title": "Меню без учёта остатков",
        "problem3_text": "План еды строится спонтанно, и продукты, которые скоро испортятся, остаются нетронутыми.",
        "goal_eyebrow": "Цель продукта",
        "goal_title": "Меньше денег на выброшенную еду и меньше отходов",
        "goal_text": "FridgeKeeper снижает траты на повторные покупки и количество выброшенной еды: вы видите остатки и успеваете их съесть.",
        "steps_eyebrow": "Как это работает",
        "steps_title": "Три шага без лишних действий",
        "step1_title": "Добавьте продукт",
        "step1_text": "Сфотографируйте этикетку или введите название вручную.",
        "step2_title": "Мы следим за сроком",
        "step2_text": "Дата «Годен до» сохраняется, а бот напоминает за пару дней.",
        "step3_title": "Планируйте по остаткам",
        "step3_text": "Смотрите, что нужно съесть первым, и не покупайте лишнего.",
        "final_title": "Начните с холодильника, который помнит за вас",
        "footer_tagline": "FridgeKeeper · Food Waste at Home",
        "app_page_title": "FridgeKeeper — веб-приложение скоро",
        "app_title": "Веб-приложение скоро появится",
        "app_text": "Веб-интерфейс FridgeKeeper в разработке. Пока продукты можно добавлять через Telegram-бота.",
        "app_back": "На главную",
        "app_bot": "Открыть бота",
    },
    "en": {
        "html_lang": "en",
        "page_title": "FridgeKeeper — expiry date tracking",
        "meta_description": "FridgeKeeper remembers what's in your fridge and reminds you before food goes bad.",
        "brand": "FridgeKeeper",
        "lang_switch": "Русский",
        "nav_open": "Open the app",
        "hero_eyebrow": "Food Waste at Home",
        "hero_title_pre": "Keep track of",
        "hero_title_hl": "expiry dates",
        "hero_title_post": "and stop throwing food away",
        "hero_sub": "FridgeKeeper remembers what's in your fridge and reminds you before food goes bad. Add items from a label photo or by hand.",
        "cta_primary": "Open FridgeKeeper",
        "cta_secondary": "Connect Telegram",
        "problems_eyebrow": "The problem",
        "problems_title": "Why food goes to waste at home",
        "problem1_title": "Blind spots in the fridge",
        "problem1_text": "We buy what we already have because we forgot about the item on the back shelf.",
        "problem2_title": "No expiry tracking",
        "problem2_text": "Dates on packaging are easy to miss, and there are usually no automatic reminders.",
        "problem3_title": "Menus ignore what you have",
        "problem3_text": "Meals get planned on the fly, and items about to expire stay untouched.",
        "goal_eyebrow": "Our goal",
        "goal_title": "Less money and food wasted",
        "goal_text": "FridgeKeeper cuts repeat purchases and thrown-away food: you see what you have and eat it in time.",
        "steps_eyebrow": "How it works",
        "steps_title": "Three steps, no extra effort",
        "step1_title": "Add a product",
        "step1_text": "Snap a photo of the label or type the name in.",
        "step2_title": "We track the date",
        "step2_text": "The best-before date is saved, and the bot reminds you a few days ahead.",
        "step3_title": "Plan around what you have",
        "step3_text": "See what to eat first and skip buying extras.",
        "final_title": "Start with a fridge that remembers for you",
        "footer_tagline": "FridgeKeeper · Food Waste at Home",
        "app_page_title": "FridgeKeeper — web app coming soon",
        "app_title": "The web app is coming soon",
        "app_text": "The FridgeKeeper web interface is in progress. For now, add products through the Telegram bot.",
        "app_back": "Back to home",
        "app_bot": "Open the bot",
    },
}


def normalize_lang(value: str | None) -> str | None:
    """Вернуть код языка, если он поддерживается, иначе None."""
    if value and value.lower() in SUPPORTED_LANGS:
        return value.lower()
    return None


def get_texts(lang: str) -> dict[str, str]:
    return TEXTS.get(lang, TEXTS[DEFAULT_LANG])
