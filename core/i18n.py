"""Тексты лендинга на русском и английском языках.

Все строки интерфейса живут здесь. Ключи с префиксом ``js_`` и группы
``hero_preview_*``, ``prod_*``, ``info_*`` передаются в браузер для демо
(см. ``get_js_strings`` и ``static/js/effects.js``).
"""

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
        "nav_open": "Открыть приложение",
        "footer_tagline": "FridgeKeeper · Меньше отходов дома",
        "aria_logo_home": "FridgeKeeper, на главную",

        # Hero
        "hero_title": "Сроки годности под контролем",
        "hero_sub": "FridgeKeeper помнит, что лежит в холодильнике, и напоминает до того, как продукт испортится. Добавляйте товары по фото этикетки или вручную.",
        "cta_primary": "Открыть FridgeKeeper",
        "cta_secondary": "Подключить Telegram",
        "hero_preview_label": "Пример холодильника",
        "hero_preview_title": "Холодильник",
        "hero_preview_count": "Продуктов: {n}",
        "hero_preview_hint": "Нажмите на продукт, чтобы увидеть подсказку.",
        "hero_preview_default_info": "Выберите продукт, чтобы увидеть, что с ним делать.",
        "hero_eyebrow": "Холодильник под присмотром",
        "hero_title_pre": "Знайте, что испортится",
        "hero_title_hl": "раньше",
        "hero_title_post": ", чем вы заметите",


        # Демо-холодильник: продукты
        "prod_milk": "Молоко",
        "prod_cheese": "Сыр",
        "prod_yogurt": "Йогурт",
        "prod_eggs": "Яйца",
        "prod_bread": "Хлеб",
        "prod_eggs_count": "Яйца · 4",
        "info_milk": "Молоко открыто 3 дня назад. Запаса ещё на 5 дней, всё в порядке.",
        "info_cheese": "Сыр скоро испортится. Бот напомнит за день, а из сыра можно приготовить ужин сегодня.",
        "info_yogurt": "Йогурт свежий, срок ещё 6 дней. Можно не спешить.",
        "info_eggs": "Яйца: 4 штуки, срок ещё 9 дней.",
        "info_bread": "Хлеб испортится завтра. Съешьте сегодня или уберите в морозилку.",

        # Демо: единицы и статусы
        "js_days_fmt": "{n} дн",
        "js_today": "сегодня",
        "js_count_fmt": "Продуктов: {n}",

        # Problem
        "problems_eyebrow": "Проблема",
        "problems_title": "Почему еда портится дома",
        "problem1_title": "Слепые зоны холодильника",
        "problem1_text": "Покупаем то, что уже есть, потому что забыли о продукте на задней полке.",
        "problem2_title": "Нет контроля сроков",
        "problem2_text": "Даты на упаковках легко пропустить, а автоматических напоминаний обычно нет.",
        "problem3_title": "Меню без учёта остатков",
        "problem3_text": "План еды строится спонтанно, и продукты, которые скоро испортятся, остаются нетронутыми.",

        # Этикетка молока
        "label_brand": "MOLOKO",
        "label_name": "Молоко пастеризованное",
        "label_volume": "1 л · 3,2%",
        "label_ingredients_key": "Состав",
        "label_ingredients_val": "молоко коровье, стабилизатор",
        "label_energy_key": "Энергия",
        "label_energy_val": "64 ккал / 100 мл",
        "label_opened_key": "Открыт",
        "label_opened_val": "3 дня назад",
        "label_best_key": "Годен до",
        "label_best_val": "14.11.2026",
        "label_left_key": "Остаток",
        "label_left_val": "250 мл",

        # Цель
        "goal_eyebrow": "Цель продукта",
        "goal_title": "Меньше денег на выброшенную еду и меньше отходов",
        "goal_text": "FridgeKeeper снижает траты на повторные покупки и количество выброшенной еды: вы видите остатки и успеваете их съесть.",

        # Шаги
        "steps_eyebrow": "Как это работает",
        "steps_title": "Три шага без лишних действий",
        "step1_title": "Добавьте продукт",
        "step1_text": "Сфотографируйте этикетку или введите название вручную. Категорию и типичный срок хранения подставим сами.",
        "step2_title": "Мы следим за сроком",
        "step2_text": "Дата «Годен до» сохраняется, а бот напоминает за пару дней до истечения.",
        "step3_title": "Планируйте по остаткам",
        "step3_text": "Смотрите, что нужно съесть первым, и не покупайте лишнего.",
        "mini_zone1": "01 · Добавить",
        "mini_zone2": "02 · Срок",
        "mini_zone3": "03 · Остатки",
        "mini_milk": "Молоко",
        "mini_yogurt": "Йогурт",
        "mini_cheese": "Сыр",
        "mini_days_soon": "2 дн",
        "mini_curd": "Творог",
        "mini_bread": "Хлеб",
        "mini_eggs": "Яйца · 4 шт",

        # Всё связано
        "connected_eyebrow": "Всё связано",
        "connected_title": "Один холодильник, одна картина",
        "connected_lead": "Продукты, сроки и остатки в одном месте, и всё обновляется само.",
        "feature1_title": "Ведём остатки",
        "feature1_text": "Списываем продукт, когда он закончился, а не когда вы заметили.",
        "feature2_title": "Сроки под контролем",
        "feature2_text": "Напоминания приходят до того, как продукт испортится.",
        "feature3_title": "Покупки по плану",
        "feature3_text": "Список покупок учитывает то, что уже лежит в холодильнике.",
        "fp1_a": "Молоко",
        "fp1_a_val": "списано 250 мл",
        "fp1_b": "Хлеб",
        "fp1_b_val": "остаток 0",
        "fp2_a": "Сыр",
        "fp2_a_val": "через 2 дня",
        "fp2_b": "Напоминание",
        "fp2_b_val": "завтра, 9:00",
        "fp3_a": "Молоко",
        "fp3_a_val": "уже есть, не покупать",
        "fp3_b": "Яйца",
        "fp3_b_val": "нужно 2 шт",

        # Финал
        "final_title": "Начните с холодильника, который помнит за вас",

        # Заглушка приложения
        "app_page_title": "FridgeKeeper — веб-приложение скоро",
        "app_title": "Веб-приложение скоро появится",
        "app_text": "Веб-интерфейс FridgeKeeper в разработке. Пока продукты можно добавлять через Telegram-бота.",
        "app_back": "На главную",
        "app_bot": "Открыть бота",

        "goal_title": "Сколько еды вы выбросили в прошлом месяце?",
        "goal_text": "Обычно ответ — то, что забыли на задней полке. FridgeKeeper помнит за вас, что и когда пора съесть.",
        "steps_eyebrow": "Как это выглядит",
        "steps_title": "Просто добавьте и забудьте",
        "connected_title": "Всё, что лежит у вас, в одном списке",
        "connected_lead": "Остатки, сроки и покупки связаны. Меняется одно, обновляется всё.",
        "final_title": "Холодильник, который помнит за вас",
        "info_milk": "Молоко открыли три дня назад. Ещё пять дней, допейте спокойно.",
    },
    "en": {
        "html_lang": "en",
        "page_title": "FridgeKeeper — expiry date tracking",
        "meta_description": "FridgeKeeper remembers what's in your fridge and reminds you before food goes bad.",
        "brand": "FridgeKeeper",
        "lang_switch": "Русский",
        "nav_open": "Open the app",
        "footer_tagline": "FridgeKeeper · Less food waste at home",
        "aria_logo_home": "FridgeKeeper, go to home",

        "goal_title": "How much food did you throw out last month?",
        "goal_text": "Usually it's whatever got forgotten on the back shelf. FridgeKeeper remembers for you what to eat and when.",
        "steps_eyebrow": "What it looks like",
        "steps_title": "Add it once and forget about it",
        "connected_title": "Everything you have, in one list",
        "connected_lead": "Stock, dates and shopping are linked. Change one thing and the rest updates.",
        "final_title": "A fridge that remembers for you",
        "info_milk": "The milk was opened three days ago. Five days left, no hurry.",

        # Hero
        "hero_title": "Expiry dates, under control",
        "hero_sub": "FridgeKeeper remembers what's in your fridge and reminds you before food goes bad. Add items from a label photo or by hand.",
        "cta_primary": "Open FridgeKeeper",
        "cta_secondary": "Connect Telegram",
        "hero_preview_label": "Fridge example",
        "hero_preview_title": "Fridge",
        "hero_preview_count": "Items: {n}",
        "hero_preview_hint": "Tap an item to see a tip.",
        "hero_preview_default_info": "Pick an item to see what to do with it.",
        "hero_eyebrow": "Your fridge, kept in view",
        "hero_title_pre": "Know what will spoil",
        "hero_title_hl": "sooner",
        "hero_title_post": "than you notice",

        # Demo fridge: items
        "prod_milk": "Milk",
        "prod_cheese": "Cheese",
        "prod_yogurt": "Yogurt",
        "prod_eggs": "Eggs",
        "prod_bread": "Bread",
        "prod_eggs_count": "Eggs · 4",
        "info_milk": "The milk was opened 3 days ago. It keeps for 5 more days, all good.",
        "info_cheese": "The cheese will go off soon. The bot reminds you a day ahead, and you could make cheese toast tonight.",
        "info_yogurt": "The yogurt is fresh with 6 days left. No rush.",
        "info_eggs": "Eggs: 4 pieces, 9 days left.",
        "info_bread": "The bread goes stale tomorrow. Eat it today or freeze it.",

        # Demo: units and statuses
        "js_days_fmt": "{n} d",
        "js_today": "today",
        "js_count_fmt": "Items: {n}",

        # Problem
        "problems_eyebrow": "The problem",
        "problems_title": "Why food goes to waste at home",
        "problem1_title": "Blind spots in the fridge",
        "problem1_text": "We buy what we already have because we forgot about the item on the back shelf.",
        "problem2_title": "No expiry tracking",
        "problem2_text": "Dates on packaging are easy to miss, and there are usually no automatic reminders.",
        "problem3_title": "Menus ignore what you have",
        "problem3_text": "Meals get planned on the fly, and items about to expire stay untouched.",

        # Milk label
        "label_brand": "MILK",
        "label_name": "Pasteurized milk",
        "label_volume": "1 l · 3.2%",
        "label_ingredients_key": "Ingredients",
        "label_ingredients_val": "cow's milk, stabilizer",
        "label_energy_key": "Energy",
        "label_energy_val": "64 kcal / 100 ml",
        "label_opened_key": "Opened",
        "label_opened_val": "3 days ago",
        "label_best_key": "Best before",
        "label_best_val": "14 Nov 2026",
        "label_left_key": "Left",
        "label_left_val": "250 ml",

        # Goal
        "goal_eyebrow": "Our goal",
        "goal_title": "Less money and food wasted",
        "goal_text": "FridgeKeeper cuts repeat purchases and thrown-away food: you see what you have and eat it in time.",

        # Steps
        "steps_eyebrow": "How it works",
        "steps_title": "Three steps, no extra effort",
        "step1_title": "Add a product",
        "step1_text": "Snap a photo of the label or type the name in. We fill in the category and typical shelf life.",
        "step2_title": "We track the date",
        "step2_text": "The best-before date is saved, and the bot reminds you a few days ahead.",
        "step3_title": "Plan around what you have",
        "step3_text": "See what to eat first and skip buying extras.",
        "mini_zone1": "01 · Add",
        "mini_zone2": "02 · Date",
        "mini_zone3": "03 · Stock",
        "mini_milk": "Milk",
        "mini_yogurt": "Yogurt",
        "mini_cheese": "Cheese",
        "mini_days_soon": "2 d",
        "mini_curd": "Cottage cheese",
        "mini_bread": "Bread",
        "mini_eggs": "Eggs · 4 pcs",

        # Connected
        "connected_eyebrow": "Connected",
        "connected_title": "One fridge, one picture",
        "connected_lead": "Items, dates and stock in one place, and everything updates on its own.",
        "feature1_title": "Track stock",
        "feature1_text": "We remove an item when it runs out, not when you notice.",
        "feature2_title": "Dates under control",
        "feature2_text": "Reminders arrive before the food goes bad.",
        "feature3_title": "Shopping to plan",
        "feature3_text": "The shopping list accounts for what is already in your fridge.",
        "fp1_a": "Milk",
        "fp1_a_val": "used 250 ml",
        "fp1_b": "Bread",
        "fp1_b_val": "0 left",
        "fp2_a": "Cheese",
        "fp2_a_val": "in 2 days",
        "fp2_b": "Reminder",
        "fp2_b_val": "tomorrow, 9:00",
        "fp3_a": "Milk",
        "fp3_a_val": "already have it, don't buy",
        "fp3_b": "Eggs",
        "fp3_b_val": "need 2 more",

        # Final
        "final_title": "Start with a fridge that remembers for you",

        # App placeholder
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


def get_js_strings(lang: str) -> dict[str, str]:
    """Строки, нужные скриптам в браузере демо-холодильника."""
    texts = get_texts(lang)
    prefixes = ("js_", "hero_preview_", "prod_", "info_")
    return {k: v for k, v in texts.items() if k.startswith(prefixes)}
