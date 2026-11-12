# Контекст проекта FridgeKeeper

## Кто я и как работать
- Пишу на Python, в дизайне новичок. Система Windows 10/11, команды в PowerShell (PS 5). Путь проекта: `C:\Users\User\Desktop\FridgeKeeper`.
- Отвечать по-русски.
- Перед кодом сначала план и вопросы, если идея или правка кажется нелогичной или противоречит проекту. Потом выполнять.
- Ошибки присылать полным текстом из консоли, не пересказом.
- Часовой пояс: Asia/Almaty (UTC+5). Текущая дата: 12.11.2026.

## Что строим
Сервис контроля сроков годности продуктов в Казахстане.
- **Бот** Telegram: `@FridgeKeeper_MESSAGE_BOT`, aiogram 3. Команды `/start`, `/help`, `/my_products`, `/add`.
- **Сайт** FastAPI + Jinja2: лендинг RU/EN, `/login` (вход через Telegram Login Widget), `/app` (заглушка), `/mini` (страница Mini App).
- **Камера**: распознавание этикетки через Yandex Vision (OCR), фото не сохраняется.
- **Уведомления** через бота за 24, 12, 6, 2 часа до дедлайна.
- **База**: PostgreSQL 18 на ПК, пользователь `fridgekeeper`, базы `fridgekeeper` и `fridgekeeper_test`. Alembic, миграция `0001` применена.
- **Хостинг**: API, бот и планировщик работают на ПК. Доступ снаружи через Cloudflare quick tunnel (адрес меняется при каждом запуске). Лендинг задеплоен на Vercel: `https://fridge-keeper-eight.vercel.app`, это FastAPI-приложение, отдельное от ПК.

## Принятые решения
| Тема | Решение |
|---|---|
| Данные | Хранятся в PostgreSQL в Казахстане. Фото уходит в Yandex Vision и Vercel за пределы страны. Пользователь это принял. |
| Дедлайн | 00:00 дня, следующего за датой на этикетке. «Годен до 12.05» → дедлайн 13.05 00:00 |
| Уведомления | Один раз на уровень. Если уровни пропущены (ПК был выключен), одно сообщение для самого срочного, остальные помечаются `skipped`. Текст показывает реальное оставшееся время. |
| Дата без подписи | Берётся самая поздняя дата на этикетке как предположение. Показывается пользователю с пометкой. |
| Просроченный продукт | Показывается с предупреждением. Сохранить можно после подтверждения. |
| Название продукта | Из словаря `KNOWN_PRODUCTS`. Пользователь подтверждает кнопками «Да» / «Нет, введу сам». |
| Фото | Не сохраняются, читаются в памяти. |
| Вход на сайт | Login Widget → cookie `fk_session` (httponly, secure, samesite=lax). |
| Вход в Mini App | `initData` → `POST /auth/mini-app` → токен в JSON → заголовок `Authorization: Bearer`. Cookie не используется. |
| Mini App | Страница `/mini` отдаётся с ПК через туннель. CORS и адрес Vercel для Mini App не нужны. Vercel остаётся под лендинг. |
| Сессии | Хранятся в памяти процесса `SESSIONS`. После перезапуска uvicorn все сессии пропадают. Позже перенести в БД. |
| Планировщик | APScheduler (`AsyncIOScheduler`) в `core/scheduler.py`, в том же процессе, что и бот. Проверка каждые 5 минут. |

## Что сделано и работает
- **Вход на сайт** через `/login`: подтверждено, `/app` открывается.
- **Вход в Mini App**: подтверждено, в консоли всё правильно.
- **Тесты**: 37 тестов проходили до последних правок (проверить снова).
- **OCR**: `scripts/check_ocr.py` на фото `test.png` (упаковка йогурта Natige) возвращает текст. Название «Йогурт», дата `2026-11-10` (предположение), предупреждение «срок уже истёк».
- **Эндпоинты продуктов** (`api/products.py`):
  - `POST /products/scan` — принимает файл, возвращает `product_name`, `expiry_date`, `confidence`, `expired`. Не сохраняет.
  - `POST /products` — сохраняет подтверждённый продукт (`name`, `expiry_date`, `expiry_source` = `ocr` | `manual` | `bot`).
  - `GET /products` — список продуктов пользователя.
- **Проверка 401** без cookie на `/products`: работает.
- **Первый вызов** `/products/scan` через туннель вернул `200 OK`.

## Текущая проблема (на чём остановились)
Второй вызов `POST /products/scan` через туннель завис. Cloudflare вернул **524 (timeout)**. Тело ответа в `result.json` — страница ошибки Cloudflare, а не JSON.

Возможные причины, по убыванию вероятности:
1. Запрос к Yandex Vision (`core/ocr.py`, `httpx`, timeout 20 с) завис или отвечает долго.
2. Запрос не дошёл до uvicorn (туннель).
3. Зависание в обработке файла или в БД.

**Что сделать первым делом:** посмотреть лог uvicorn за время запроса. Если строки `POST /products/scan 200 OK` нет, а ошибка есть, пришлите трейсбек. Если сервер тихо — проверить Yandex напрямую через `scripts/check_ocr.py test.png`, он работает локально без туннеля.

## Безопасность
- Значение cookie `fk_session` несколько раз попадало в чат. Чтобы аннулировать, перезапустить uvicorn (сессии в памяти). Новый cookie в чат не присылать.

## Структура проекта (ключевое)
```
FridgeKeeper\
├── .env                      TELEGRAM_TOKEN, YANDEX_API_KEY, YANDEX_FOLDER_ID, DATABASE_URL
├── pyproject.toml            (нужно добавить python-multipart)
├── app.py                    FastAPI: CORS, роутеры auth и products, маршруты /, /login, /app, /mini
├── api\
│   ├── __init__.py           пустой
│   ├── auth.py               /auth/login-widget, /auth/mini-app, /auth/me, current_user_id
│   └── products.py           /products/scan, POST /products, GET /products
├── bot\                      __init__, formatting, handlers, main (init_db() пока не удалён)
├── core\
│   ├── config.py             читает .env; DATABASE_URL по умолчанию SQLite (проверить .env!)
│   ├── database.py           engine, SessionFactory, init_db
│   ├── telegram_auth.py      verify_login_widget, verify_mini_app
│   ├── users.py              get_or_create_user, create_web_user
│   ├── products.py           list_user_products
│   ├── ocr.py                recognize_text (Yandex Vision, языки ru, en)
│   ├── expiry_parser.py      parse_expiry (по маркерам), parse_expiry_guess (поздняя дата)
│   ├── product_names.py      KNOWN_PRODUCTS, find_product_name
│   ├── label_service.py      analyze_label → LabelResult(text, product_name, expiry_date, confidence)
│   ├── linking.py            токены связки сайт ↔ Telegram
│   ├── notifications.py      TZ, deadline_for, decide, build_message
│   └── i18n.py               тексты RU/EN, login_title/login_hint уже есть в обоих языках
├── models\                   base, user, product (с expiry_source), link_token, notification
├── migrations\               env.py, versions\0001_initial.py (expiry_source уже есть)
├── scripts\
│   ├── migrate_sqlite_to_pg.py
│   └── check_ocr.py          проверка OCR на фото без сайта
├── templates\                base.html, landing.html, login.html, app_placeholder.html, mini.html
├── static\                   css\landing.css, js\effects.js
├── tests\                    conftest.py (пароль БД пока в коде), test_*.py
└── instance\                 database.db (старая SQLite, не используется)
```

## Файлы, которые нужно положить в проект (из последних правок)
- `app.py` — заменить
- `api\auth.py` — заменить
- `api\products.py` — новый
- `core\product_names.py` — новый
- `core\label_service.py` — заменить
- `core\expiry_parser.py` — заменить
- `scripts\check_ocr.py` — новый
- `templates\mini.html` — новый
- `templates\login.html` — заменить (исправлен `data-auth-url`, убран лишний символ)
- `core\i18n.py` — заменить (подсказка входа «Нажмите кнопку ниже, чтобы войти»)

Все файлы лежат в `/mnt/user-data/outputs/` в той среде, где они создавались. В Codex их нужно скопировать в проект из загрузок или заново сгенерировать по описанию выше.

## Чек-лист перед продолжением
1. `uv add python-multipart` (без неё `api/products.py` не загрузится).
2. В `.env` есть `DATABASE_URL=postgresql+asyncpg://fridgekeeper:ПАРОЛЬ@127.0.0.1:5432/fridgekeeper`, и установлен `asyncpg`. Иначе приложение пишет в SQLite по умолчанию.
3. Запуск uvicorn:
   ```
   uv run uvicorn app:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips="*"
   ```
4. Туннель: `.\cloudflared.exe tunnel --url http://127.0.0.1:8000`. Новый адрес → `/setdomain` и `/newapp` в BotFather.
5. Тесты: `uv run pytest` (ожидаем 37+).

## Открытые задачи (по порядку)
1. **Разобрать 524 на `/products/scan`** (см. выше). Статус: OCR локально отвечает за ~2 с, значит, зависание, скорее всего, в туннеле или в запросе из браузера. Нужен лог uvicorn за время запроса (в терминале PowerShell его нет, uvicorn запущен отдельно).
2. ✅ Сделано 12.11: `POST /products` и `GET /products` проверены тестами `tests\test_products_api.py` (через временную SQLite).
3. ✅ Сделано 12.11: `PATCH /products/{id}` (имя, срок, `null` убирает срок) и `DELETE /products/{id}`. Чужой продукт даёт 404. Тесты в `tests\test_products_api.py`.
3a. **Страница камеры в `/mini`**:
   - кнопка «Сфотографировать» (или выбор файла);
   - отправка на `/products/scan`;
   - показ названия и даты с кнопками «Да» / «Нет, введу сам»;
   - предупреждение «срок уже истёк», если `expired: true`;
   - сохранение через `POST /products` с `expiry_source` = `ocr` или `manual`.
4. ✅ Сделано 12.11: команда `/add Название; ДД.ММ.ГГГГ` в боте (дата необязательна), `parse_add_args` в `bot\handlers.py`, тесты `tests\test_add_command.py`, строка в `/help`. Ручной ввод срока на сайте (в `/app`) ещё не сделан.
5. ✅ Сделано 12.11: планировщик `core/scheduler.py` (проверка каждые 5 мин, отправка через бота, запись в `notification_log`). Запускается из `bot\main.py`. Тесты `tests\test_scheduler.py`. Не проверено в живом боте: нужен реальный Telegram-чат.
6. ✅ Сделано 12.11: `init_db()` удалён из `bot\main.py`. Схему создаёт Alembic.
7. ✅ Сделано 12.11: пароль тестовой БД вынесен из `tests\conftest.py` в `.env` (`TEST_DATABASE_URL`).
8. ✅ 12.11: поиск «Test yogurt» дал 0 строк в `fridgekeeper` (PostgreSQL), в `fridgekeeper_test` таблицы `products` нет, в `instance\database.db` тоже 0 строк. Удалять нечего. Если строка всё же появилась, проверить вручную.
9. Постоянный домен туннеля (именованный cloudflared), чтобы не перенастраивать BotFather при каждом запуске.
10. Перенести сессии из памяти в БД.
11. Решить судьбу сайта на Vercel: сейчас это отдельное FastAPI-приложение без связи с ПК. Либо оставить под лендинг, либо привести в соответствие.

## Правило ведения журнала (с 12.11.2026)
- После каждой выполненной задачи дописывать запись в раздел «Журнал работы» ниже: дата, что сделано, результат проверки (вывод команды), что осталось.
- Использование graphify (карта кода) тоже фиксировать в журнале: что спрашивали у карты и что дала, либо почему не использовали.
- Любое изменение правил в этом файле фиксировать в «Журнал работы» строкой «Правило изменено: …».

## Graphify (карта проекта)
- Карта: `graphify-out\graph.html` и `graphify-out\graph.json`. Вызов: `/graphify`, инструкция в `C:\Users\User\.Codex\skills\graphify\SKILL.md`.
- Для вопросов про структуру кода сначала смотреть карту, потом читать файлы.

## Журнал работы
- **12.11.2026, задача «что осталось для бэкенда»**: составлен список из 9 пунктов (ответ в чате). Карта graphify не использовалась, список собран по grep.
- **12.11.2026, шаг 2 «тесты»**: `uv run pytest -q` → `37 passed, 1 warning in 2.17s`.
- **12.11.2026, шаг 1 «524 на /products/scan»**: `uv run python scripts/check_ocr.py test.png` сначала упал на печати казахских букв в cp1251. Исправлено: `sys.stdout.reconfigure(encoding="utf-8")` в [scripts/check_ocr.py](scripts/check_ocr.py). После правки: распознан текст «ÍOGURT», название «Йогурт», дата 2026-11-10 (предположение), время ~2 с. Причина 524 не найдена: нужен лог uvicorn.
- **12.11.2026, правило**: добавлены разделы «Правило ведения журнала», «Graphify» и этот журнал по запросу пользователя.
- **12.11.2026, туннель отложен** по решению пользователя. Пункты, которые требуют туннеля (524, UI камеры в `/mini`), не делались.
- **12.11.2026, пункты 1, 2, 5, 7 плана**:
  - удалён `init_db()` из `bot\main.py`; добавлен запуск `run_forever` планировщика;
  - пароль тестовой БД перенесён в `.env` (`TEST_DATABASE_URL`), `tests\conftest.py` читает его через `load_dotenv`;
  - новый `core\scheduler.py` (`check_once`, `run_forever`), тесты `tests\test_scheduler.py` (5 шт.);
  - тесты `tests\test_products_api.py` (4 шт.) для `POST` и `GET /products`.
  - Результат: `uv run pytest -q` → `46 passed, 1 warning in 2.62s`. `import bot.main, core.scheduler` → `imports OK`.
  - Не сделано: пункты 3, 4, 6 из плана (`DELETE`/`PATCH` продукта, `/add`, удаление `Test yogurt`), они требуют отдельного подтверждения.
  - Смена пароля `fridgekeeper` в PostgreSQL не выполнена, пароль в `.env` и в истории чата прежний.
- **12.11.2026, APScheduler вернули** по решению пользователя: `apscheduler==3.11.3` добавлен через `uv add`, `core\scheduler.py` переписан на `AsyncIOScheduler` (`start_scheduler`), `bot\main.py` вызывает его и останавливает в `finally`. Тест `test_start_scheduler_registers_one_job_and_stops`.
- **12.11.2026, пункты 3 и 4 плана**: `PATCH`/`DELETE /products/{id}` (тесты 6 шт.), команда `/add` с `parse_add_args` (тесты 6 шт.), строка `/add` в справке.
- **12.11.2026, результат**: `uv run pytest -q` → `58 passed, 1 warning in 6.28s`. `import bot.main` → `imports OK`.
- **12.11.2026, ошибки инструмента**: хук GateGuard несколько раз блокировал правки и создание файлов; каждый раз правка повторялась после описания фактов. Одна правка `api\products.py` (импорт `Response`) не применилась с первого раза — проверено повторным запуском тестов.
- **12.11.2026, пункт 8**: подтверждение на удаление получено, но строка «Test yogurt» не найдена ни в одной БД. Удаление не выполнено, данные не менялись.
- **12.11.2026, исправлен `.env`**: строка `DATABASE_URL` была склеена с `TEST_DATABASE_URL` (из-за `Add-Content` без перевода строки), из-за этого подключение к основной БД падало. Строки разделены, проверено: `DATABASE_URL` указывает на `127.0.0.1:5432/fridgekeeper`. Пароль из старого `.env` появился в выводе команды проверки, его сменили в PostgreSQL и в `.env` (значение не записано).
- **12.11.2026, починка `.env`**: первый `Add-Content` из PowerShell не записал строку в `.env` (хотя сообщил «added»). Строка добавлена через Bash, проверено, что в `.env` 5 ключей.
- **12.11.2026, пункт 3a «Камера в /mini»**: `templates\mini.html` дополнен: кнопка «Сфотографировать» (`capture=environment`), запрос на `/products/scan` с токеном из памяти страницы, поля «Название» и «Годен до», предупреждение «Срок уже истёк», кнопки «Да» (источник `ocr`, если значения не менялись, иначе `manual`) и «Нет, введу сам» (поля очищаются). Сохранение через `POST /products`.
  - Результат: `uv run pytest -q` → `58 passed, 1 warning in 5.84s`. `TestClient` на `/mini` → `200`, в HTML есть блок камеры и пути `/products/scan`, `/products`.
  - Не проверено: сценарий в Telegram (нужен `initData` из живого Mini App и туннель). Нужна ручная проверка после запуска туннеля.
  - Предупреждение security-guidance про `integrity=` для скрипта Telegram не применено: `telegram.org/js/telegram-web-app.js` обновляется самим Telegram, фиксированного hash нет.

## Нерешённые вопросы и риски
- Законность обработки данных за пределами Казахстана: решение принято, но юридически не проверено специалистом.
- Словарь продуктов небольшой: продукты вне словаря вводятся вручную.
- Распознавание казахских этикеток: в `ocr.py` указаны только `ru` и `en`, возможно стоит добавить `kk`.
- Ссылка «Подключить Telegram» на главной ведёт в бота, а не на `/login`. Это принято, решение о смене отложено.