"""Тексты лендинга на русском и английском языках.

Ключи с префиксом ``js_`` и группы ``hero_preview_*``, ``prod_*``, ``info_*``
передаются в браузер для демо-холодильника (см. ``get_js_strings``).
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
        "theme_label": "Переключить тему",

        # Hero
        "hero_eyebrow": "Холодильник под присмотром",
        "hero_title_pre": "Знайте, что испортится",
        "hero_title_hl": "раньше",
        "hero_title_post": ", чем вы заметите",
        "hero_sub": "FridgeKeeper помнит, что лежит в холодильнике, и напоминает до того, как продукт испортится. Добавляйте товары по фото этикетки или вручную.",
        "cta_primary": "Открыть FridgeKeeper",
        "cta_secondary": "Подключить Telegram",

        # Демо-холодильник
        "hero_preview_label": "Пример холодильника",
        "hero_preview_title": "Холодильник",
        "hero_preview_hint": "Нажмите на продукт, чтобы увидеть подсказку.",
        "hero_preview_default_info": "Выберите продукт, чтобы увидеть, что с ним делать.",
        "prod_milk": "Молоко",
        "prod_cheese": "Сыр",
        "prod_yogurt": "Йогурт",
        "prod_eggs": "Яйца",
        "prod_bread": "Хлеб",
        "info_milk": "Молоко открыли три дня назад. Ещё пять дней, допейте спокойно.",
        "info_cheese": "Сыр скоро испортится. Бот напомнит за день, а из сыра можно приготовить ужин сегодня.",
        "info_yogurt": "Йогурт свежий, срок ещё 6 дней. Можно не спешить.",
        "info_eggs": "Яйца: 4 штуки, срок ещё 9 дней.",
        "info_bread": "Хлеб испортится завтра. Съешьте сегодня или уберите в морозилку.",
        "js_days_fmt": "{n} дн",
        "js_today": "сегодня",
        "js_count_fmt": "Продуктов: {n}",

        # Проблема
        "problems_eyebrow": "Проблема",
        "problems_title": "Почему еда портится дома",
        "problem1_title": "Слепые зоны",
        "problem1_text": "Покупаем то, что уже есть, потому что забыли о продукте на задней полке.",
        "problem2_title": "Сроки без контроля",
        "problem2_text": "Даты на упаковках легко пропустить, а автоматических напоминаний обычно нет.",
        "problem3_title": "Меню без остатков",
        "problem3_text": "План еды строится на ходу, и продукты, которые скоро испортятся, остаются нетронутыми.",

        # Этикетка
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
        "goal_title": "Сколько еды вы выбросили в прошлом месяце?",
        "goal_text": "Обычно ответ — то, что забыли на задней полке. FridgeKeeper помнит за вас, что и когда пора съесть.",

        # Шаги
        "steps_eyebrow": "Как это выглядит",
        "steps_title": "Просто добавьте и забудьте",
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
        "connected_title": "Всё, что лежит у вас, в одном списке",
        "connected_lead": "Остатки, сроки и покупки связаны. Меняется одно, обновляется всё.",
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

        # Telegram-бот
        "bot_eyebrow": "Telegram-бот",
        "bot_title": "Напишет первым, когда пора",
        "bot_text": "Пока веб-приложение в разработке, всё работает через бота: добавляйте продукты, спрашивайте остатки, получайте напоминания.",
        "bot_user1": "добавь молоко, открыл сегодня",
        "bot_reply1": "Молоко добавлено. Годен примерно до 17 ноября, напомню за день.",
        "bot_user2": "что скоро испортится?",
        "bot_reply2": "Хлеб сегодня, сыр через 2 дня. Сыр лучше съесть на ужин.",

        # Отзывы (примеры)
        "reviews_eyebrow": "Истории",
        "reviews_title": "Как им пользуются",
        "reviews_note": "Это примеры, реальных отзывов пока нет. Замените их своими историями.",
        "review1_text": "Раньше каждую неделю выкидывала хлеб. Теперь бот пишет за день, и хлеб съедается.",
        "review1_name": "Аня",
        "review1_role": "семья с двумя детьми",
        "review2_text": "Не ищу в голове, что купить. Список покупок уже учитывает то, что лежит в холодильнике.",
        "review2_name": "Игорь",
        "review2_role": "живёт один",
        "review3_text": "Фото этикетки вместо ручного ввода. Пять секунд, и срок уже в системе.",
        "review3_name": "Марина",
        "review3_role": "готовит на неделю вперёд",

        # FAQ
        "faq_eyebrow": "Вопросы",
        "faq_title": "Что обычно спрашивают",
        "faq1_q": "Нужно ли фото каждой этикетки?",
        "faq1_a": "Нет. Можно ввести название вручную, а срок хранения подставим по категории. Фото нужно, чтобы точнее взять дату.",
        "faq2_q": "Что вы храните о продуктах?",
        "faq2_a": "Только то, что нужно для напоминаний: название продукта, дату и остаток.",
        "faq3_q": "Работает ли без Telegram?",
        "faq3_a": "Пока работает через бота. Веб-версия в разработке, войти в неё будет тем же аккаунтом.",
        "faq4_q": "Это платный сервис?",
        "faq4_a": "Проект некоммерческий, поэтому подписок и тарифов нет.",

        # Финал
        "final_title": "Холодильник, который помнит за вас",
        "final_text": "Добавьте первый продукт прямо сейчас. Это займёт меньше минуты.",
        "final_small1": "Некоммерческий проект",
        "final_small2": "Работает в Telegram",
        "final_small3": "Меньше отходов дома",

        # Заглушка приложения
        "app_page_title": "FridgeKeeper — веб-приложение скоро",
        "app_title": "Веб-приложение скоро появится",
        "app_text": "Веб-интерфейс FridgeKeeper в разработке. Пока продукты можно добавлять через Telegram-бота.",
        "app_back": "На главную",
        "app_bot": "Открыть бота",

        "fridge_door_left": "Открыть левую дверцу",
        "fridge_door_right": "Открыть правую дверцу",
        "marquee_1": "made by emeko-emeko",
        "marquee_2": "for NOTAR ACADEMY SELECTION HACKATHON",
        "shelf_milk_hint": "Молоко · 5 дн",
        "shelf_yogurt_hint": "Йогурт · 6 дн",
        "shelf_cheese_hint": "Сыр · 2 дн",
        "shelf_bread_hint": "Хлеб · сегодня или завтра",
        "shelf_eggs_hint": "Яйца · 9 дн",
        "shelf_juice_hint": "Сок · 12 дн",
        "shelf_butter_hint": "Масло · 20 дн",
        "shelf_tomato_hint": "Помидоры · 4 дн",

        "shelf_sausage_hint": "Колбаса · 7 дн",
        "shelf_cucumber_hint": "Огурцы · 5 дн",
        "shelf_broccoli_hint": "Брокколи · 4 дн",
        "shelf_greens_hint": "Зелень · 3 дн",
        "shelf_candy_hint": "Конфеты · 120 дн",
        "shelf_chocolate_hint": "Шоколад · 180 дн",
        "shelf_ketchup_hint": "Кетчуп · 40 дн",
        "shelf_mayo_hint": "Майонез · 30 дн",
        "shelf_soda_hint": "Газировка · 90 дн",
        "shelf_mustard_hint": "Горчица · 180 дн",
        "shelf_water_hint": "Вода · 300 дн",
        "shelf_kefir_hint": "Кефир · 8 дн",
        "shelf_jam_hint": "Варенье · 200 дн",
        "shelf_pickles_hint": "Маринованные огурцы · 60 дн",
        "login_title": "Вход с помощью Telegram",
        "login_hint": "Нажмите кнопку ниже, чтобы войти"
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
        "theme_label": "Switch theme",

        # Hero
        "hero_eyebrow": "Your fridge, kept in view",
        "hero_title_pre": "Know what will spoil",
        "hero_title_hl": "sooner",
        "hero_title_post": "than you notice",
        "hero_sub": "FridgeKeeper remembers what's in your fridge and reminds you before food goes bad. Add items from a label photo or by hand.",
        "cta_primary": "Open FridgeKeeper",
        "cta_secondary": "Connect Telegram",

        # Demo fridge
        "hero_preview_label": "Fridge example",
        "hero_preview_title": "Fridge",
        "hero_preview_hint": "Tap an item to see a tip.",
        "hero_preview_default_info": "Pick an item to see what to do with it.",
        "prod_milk": "Milk",
        "prod_cheese": "Cheese",
        "prod_yogurt": "Yogurt",
        "prod_eggs": "Eggs",
        "prod_bread": "Bread",
        "info_milk": "The milk was opened three days ago. Five days left, no hurry.",
        "info_cheese": "The cheese will go off soon. The bot reminds you a day ahead, and you could make cheese toast tonight.",
        "info_yogurt": "The yogurt is fresh with 6 days left. No rush.",
        "info_eggs": "Eggs: 4 pieces, 9 days left.",
        "info_bread": "The bread goes stale tomorrow. Eat it today or freeze it.",
        "js_days_fmt": "{n} d",
        "js_today": "today",
        "js_count_fmt": "Items: {n}",

        # Problem
        "problems_eyebrow": "The problem",
        "problems_title": "Why food goes to waste at home",
        "problem1_title": "Blind spots",
        "problem1_text": "We buy what we already have because we forgot about the item on the back shelf.",
        "problem2_title": "No date tracking",
        "problem2_text": "Dates on packaging are easy to miss, and there are usually no automatic reminders.",
        "problem3_title": "Menus ignore stock",
        "problem3_text": "Meals get planned on the fly, and items about to expire stay untouched.",

        # Label
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
        "goal_title": "How much food did you throw out last month?",
        "goal_text": "Usually it's whatever got forgotten on the back shelf. FridgeKeeper remembers for you what to eat and when.",

        # Steps
        "steps_eyebrow": "What it looks like",
        "steps_title": "Add it once and forget about it",
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
        "connected_title": "Everything you have, in one list",
        "connected_lead": "Stock, dates and shopping are linked. Change one thing and the rest updates.",
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

        # Telegram bot
        "bot_eyebrow": "Telegram bot",
        "bot_title": "It messages you first, when it's time",
        "bot_text": "While the web app is in progress, everything runs through the bot: add products, ask what's left, get reminders.",
        "bot_user1": "add milk, opened today",
        "bot_reply1": "Milk added. Good until about 17 Nov, I'll remind you a day before.",
        "bot_user2": "what's going off soon?",
        "bot_reply2": "Bread today, cheese in 2 days. Cheese is best eaten at dinner.",

        # Reviews (examples)
        "reviews_eyebrow": "Stories",
        "reviews_title": "How people use it",
        "reviews_note": "These are examples, there are no real reviews yet. Replace them with your own stories.",
        "review1_text": "I used to throw out bread every week. Now the bot warns me a day ahead, and the bread gets eaten.",
        "review1_name": "Anna",
        "review1_role": "family with two kids",
        "review2_text": "I don't have to remember what to buy. The shopping list already counts what's in the fridge.",
        "review2_name": "Igor",
        "review2_role": "lives alone",
        "review3_text": "A label photo instead of typing. Five seconds and the date is in the system.",
        "review3_name": "Marina",
        "review3_role": "cooks for the whole week",

        # FAQ
        "faq_eyebrow": "Questions",
        "faq_title": "What people usually ask",
        "faq1_q": "Do I need a photo of every label?",
        "faq1_a": "No. You can type the name, and we fill in shelf life by category. A photo just gets the date more accurately.",
        "faq2_q": "What do you store about products?",
        "faq2_a": "Only what reminders need: the product name, the date and the amount left.",
        "faq3_q": "Does it work without Telegram?",
        "faq3_a": "For now it works through the bot. The web version is in progress, and you'll sign in with the same account.",
        "faq4_q": "Is it a paid service?",
        "faq4_a": "It's a non-commercial project, so there are no subscriptions or plans.",

        # Final
        "final_title": "A fridge that remembers for you",
        "final_text": "Add your first product right now. It takes less than a minute.",
        "final_small1": "Non-commercial project",
        "final_small2": "Works in Telegram",
        "final_small3": "Less food waste at home",

        # App placeholder
        "app_page_title": "FridgeKeeper — web app coming soon",
        "app_title": "The web app is coming soon",
        "app_text": "The FridgeKeeper web interface is in progress. For now, add products through the Telegram bot.",
        "app_back": "Back to home",
        "app_bot": "Open the bot",

        "fridge_door_left": "Open the left door",
        "fridge_door_right": "Open the right door",
        "marquee_1": "made by emeko-emeko",
        "marquee_2": "for NOTAR ACADEMY SELECTION HACKATHON",
        "shelf_milk_hint": "Milk · 5 d",
        "shelf_yogurt_hint": "Yogurt · 6 d",
        "shelf_cheese_hint": "Cheese · 2 d",
        "shelf_bread_hint": "Bread · today or tomorrow",
        "shelf_eggs_hint": "Eggs · 9 d",
        "shelf_juice_hint": "Juice · 12 d",
        "shelf_butter_hint": "Butter · 20 d",
        "shelf_tomato_hint": "Tomatoes · 4 d",

        "shelf_sausage_hint": "Sausage · 7 d",
        "shelf_cucumber_hint": "Cucumbers · 5 d",
        "shelf_broccoli_hint": "Broccoli · 4 d",
        "shelf_greens_hint": "Herbs · 3 d",
        "shelf_candy_hint": "Candy · 120 d",
        "shelf_chocolate_hint": "Chocolate · 180 d",
        "shelf_ketchup_hint": "Ketchup · 40 d",
        "shelf_mayo_hint": "Mayonnaise · 30 d",
        "shelf_soda_hint": "Soda · 90 d",
        "shelf_mustard_hint": "Mustard · 180 d",
        "shelf_water_hint": "Water · 300 d",
        "shelf_kefir_hint": "Kefir · 8 d",
        "shelf_jam_hint": "Jam · 200 d",
        "shelf_pickles_hint": "Pickles · 60 d",
        "login_title": "Enter with Telegram",
        "login_hint": "Press the button below to sign in"
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