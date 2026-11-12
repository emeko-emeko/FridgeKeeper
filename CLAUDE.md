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
├── templates\                base.html, landing.html, login.html, app.html, mini.html
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

Все файлы лежат в `/mnt/user-data/outputs/` в той среде, где они создавались. В Claude Code их нужно скопировать в проект из загрузок или заново сгенерировать по описанию выше.

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
- Карта: `graphify-out\graph.html` и `graphify-out\graph.json`. Вызов: `/graphify`, инструкция в `C:\Users\User\.claude\skills\graphify\SKILL.md`.
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
  - Проверка в Telegram через туннель `cloudflared\cloudflared.exe` (адрес меняется при каждом запуске): по логу uvicorn прошли `POST /auth/mini-app` → 200, `GET /auth/me` → 200, `POST /products/scan` → 200, `POST /products` → 201. Ошибки 524 в этом прогоне не было. Что на экране (название, дата, предупреждение) и `GET /products` не проверены.
  - Скриншот Mini App (12.11.2026): поля «Название» = «Йогурт», «Годен до» = 10.11.2026, показано «Срок уже истёк», кнопки «Да» и «Нет, введу сам» видны. Распознавание и предупреждение работают.
  - Не проверено: сохранение через «Да» в списке продуктов, кнопка «Нет, введу сам» (источник `manual`).
  - Адрес туннеля при этом прогоне: `cabinets-integer-occurs-sealed.trycloudflare.com`. Адрес меняется при каждом запуске `cloudflared`, в BotFather его нужно обновлять.
  - Предупреждение security-guidance про `integrity=` для скрипта Telegram не применено: `telegram.org/js/telegram-web-app.js` обновляется самим Telegram, фиксированного hash нет.
- **12.11.2026, мелочи (по подтверждению пользователя)**:
  - `core\ocr.py`: `language_codes` = `["ru", "en", "kk"]`. Единственный вызов `recognize_text`: `core\label_service.py:24`.
  - Результат: `uv run pytest -q` → `58 passed, 1 warning in 5.24s`. `uv run python scripts/check_ocr.py test.png` → «Йогурт», дата 2026-11-10 (предположение), «срок уже истёк».
  - Пункт 524 исключён из списка по решению пользователя.
  - Смена пароля `fridgekeeper` в PostgreSQL: инструкция дана, выполняет пользователь. Не подтверждено. В чат пользователь прислал строку, похожую на пароль; она не использовалась и не записана. Рекомендуется сменить её после работы.
- **12.11.2026, коммит и публикация на GitHub**:
  - Коммит `1bbc413` «Backend: products API, Mini App camera, /add command, scheduler», отправлен в `origin/main` (`https://github.com/emeko-emeko/FridgeKeeper`).
  - В коммит вошли исходники, тесты, миграции, `pyproject.toml`, `uv.lock`, `alembic.ini`, `CLAUDE.md`, `AGENTS.md`.
  - Исключены: `.env`, `instance/`, `cloudflared/`, `graphify-out/`, `result.json`, `test.png`. В `.gitignore` добавлены `cloudflared/`, `graphify-out/`, `result.json`, `test.png`, `*.dump`.
  - Перед коммитом пароль `fk_pass_2026` удалён из журнала в `CLAUDE.md` и `AGENTS.md` (заменён на «значение не записано»). Пароль остаётся в истории чата и, возможно, в истории git, если там был `.env`. Проверку истории git не делали.
  - Проверка: поиском по staged-файлам не найдено `fk_pass`, токенов Telegram и ключей Yandex (`grep exit 1`).
  - Рабочая копия после коммита чистая (`git status --short` пусто).
- **12.11.2026, итог по бэкенду**:
  - Не сделано или не проверено: смена пароля PostgreSQL (делает пользователь); сценарий Mini App в Telegram («Да», «Нет, введу сам», `GET /products`); ручной ввод срока на `/app`; живой прогон планировщика уведомлений в боте; проверка `python-multipart` (тесты с загрузкой проходят, но в `pyproject.toml` не сверяли).
  - Отложено: именованный туннель, перенос сессий из памяти в БД, судьба сайта на Vercel.
  - Следующий шаг по плану: редизайн `/mini` (после коммита), затем ручной ввод срока на `/app`, затем повторная проверка Mini App. Ждём подтверждения плана.
- **12.11.2026, проверка входа через Telegram в браузере**:
  - `GET /login` → 200, `GET /app` → 200, `GET /auth/login-widget` без параметров → 400 (сервер на 127.0.0.1:8000 запущен).
  - В браузере на `http://127.0.0.1:8000/login` виджет (iframe `oauth.telegram.org`) показывает «Bot domain invalid». Кнопки для входа нет.
  - Причина (по тексту ошибки, в документации Telegram не сверяли): виджет работает только на домене, привязанном к боту через BotFather `/setdomain`. `127.0.0.1` привязать нельзя.
  - Не проверено: вход через адрес туннеля (`*.trycloudflare.com`). Нужно, чтобы текущий адрес туннеля был привязан в `/setdomain`, и тогда проверить кнопку в браузере.
- **12.11.2026, сайт на Vercel отдаёт 500**:
  - `GET https://fridge-keeper-eight.vercel.app/` → 500, заголовок `X-Vercel-Error: FUNCTION_INVOCATION_FAILED`. Функция падает при запуске.
  - Vercel MCP не дал логи: `list_projects` → 403, команда в scope `imansuper44-2979`, `list_teams` пустой. Логи не смотрели.
  - Вероятная причина: `api/products.py` использует `File`/`UploadFile`, а `python-multipart` есть только в локальном `.venv`, но не в `requirements.txt`. Проверка: `import app` с заблокированным `multipart` выводит «pip install python-multipart».
  - Второй кандидат: `core/ocr.py` делает `import httpx`, а `httpx` нет в `requirements.txt`.
  - Исправление не применено: нужен план и подтверждение. План: добавить `python-multipart` и `httpx` в `requirements.txt`, передеплоить.
  - Исправлено по подтверждению: в `requirements.txt` добавлены `python-multipart==0.0.33`, `httpx==0.28.1`, `tzdata==2026.6`. Коммит `9b46b2e` локальный, не запушен.
  - Проверка в чистом venv из `requirements.txt` (SQLite): `import app` OK, `/` 200, `/login` 200, `/app` 200, `/mini` 200, `/products` без входа 401.
  - Не найдено при проверке: `asyncpg` нет в `requirements.txt`, а локальный `.env` указывает на PostgreSQL. Для Vercel это важно только если там задан `DATABASE_URL` с postgres.
  - Vercel после этого не проверен: `https://fridge-keeper-eight.vercel.app/` всё ещё 500. Нужен push в `origin/main`, чтобы Vercel пересобрал сайт. Push не делали: нужно подтверждение.
  - Push по подтверждению: `git push origin main` → `1bbc413..9b46b2e main -> main`. Через ~3 минуты `https://fridge-keeper-eight.vercel.app/`, `/login`, `/app` всё ещё 500 (`FUNCTION_INVOCATION_FAILED`). Статус деплоя не видно: Vercel MCP получает 403 по scope `imansuper44-2979`, `gh` не авторизован. Нужно открыть дашборд Vercel: проверить, запустился ли деплой `9b46b2e`, и build/runtime logs.
  - Доступ к Vercel дали (scope `imansuper44-2979`). Деплой `dpl_7PZSCZRorq8AUYbSoRc7gHHuQmPh` (коммит `9b46b2e`) READY, но функция падает: `ModuleNotFoundError: No module named 'fastapi'`. Vercel ставит зависимости из `pyproject.toml`, а `fastapi`, `jinja2`, `uvicorn` там не было.
  - Исправлено по подтверждению: `uv add fastapi==0.162.2 jinja2==3.1.6 uvicorn==0.54.0` (в `pyproject.toml` и `uv.lock`, `annotated-doc` 0.0.5 → 0.0.6 как транзитивная зависимость).
  - Убрано из git-индекса (файлы на диске остались): `unslop` (gitlink) и `.playwright-mcp/` (10 файлов). Оба уже были в `.gitignore`.
  - Проверка: `uv export` → чистое venv → `pip check` «No broken requirements found»; маршруты `/`, `/login`, `/app`, `/mini` 200; `/products` без входа 401. `.venv` pytest → `58 passed, 1 warning`.
  - Правило изменено: при изменении зависимостей обновлять и `requirements.txt`, и `pyproject.toml` (Vercel берёт `pyproject.toml`).
- **12.11.2026, итог сессии (вход в Telegram, Vercel, зависимости)**:
  - Вход через Telegram в браузере на `127.0.0.1:8000/login`: виджет показывает «Bot domain invalid». Причина: домен не привязан к боту через BotFather `/setdomain`. Адрес туннеля не проверен, его нужно знать заранее.
  - Vercel `https://fridge-keeper-eight.vercel.app`: 500 `FUNCTION_INVOCATION_FAILED` исправлен. Причина: в `pyproject.toml` не было `fastapi`, `jinja2`, `uvicorn`, и Vercel ставит зависимости из него. Коммиты `9b46b2e` (`requirements.txt`: `python-multipart`, `httpx`, `tzdata`) и `72873af` (`pyproject.toml`, `uv.lock`, untrack `unslop` и `.playwright-mcp`). Запушено в `origin/main`.
  - Проверка после деплоя (`dpl_G2er5rV52PfUP2AQ1KNrHEKxwkto`, READY): `/`, `/login`, `/app`, `/mini` 200. Тесты `.venv`: 58 passed.
  - Не проверено: `asyncpg` нет в `requirements.txt` (на Vercel не нужен, пока `DATABASE_URL` не postgres). Сценарий Mini App «Да»/«Нет, введу сам», `GET /products`. Ручной ввод срока на `/app`. Живой прогон планировщика в боте.
  - Vercel MCP: scope `imansuper44-2979` доступен после подтверждения. `fridgekeeper-bot` (тот же репозиторий) падает с ERROR на последних трёх коммитах. Это отдельный проект, не сайт. Не разбирали.
  - Редизайн `templates/mini.html` (по подтверждённому плану): цвета из темы Telegram (`--tg-theme-*`) с запасными значениями, крупные кнопки, блок «Проверьте данные» показывается только после распознавания, после сохранения в статусе «Сохранено: …». Логика JS не менялась (`/auth/mini-app`, `/products/scan`, `/products`, источники `ocr` / `manual`). Проверка: `.venv` pytest → `58 passed`; `/mini` → 200, в HTML есть `camera`, `snap`, `result`, `/products/scan`, кнопки «Да, сохранить» и «Нет, введу сам». Не проверено: вид в Telegram и сценарий входа на адресе туннеля (нужен живой Mini App).
  - Запушено в `origin/main`: `72873af..952ce3f` (редизайн `/mini` и журнал). Vercel после пуша не перепроверяли.
  - Рекомендации по модели и инструментам для редизайна: Sonnet 5.5 для правок, Opus 5.5 для критики и финальной полировки. Скиллы в установке: impeccable (критика и полировка), unslop (убрать «ИИ-вид»), frontend-design, vectorlab-ux-skills (`forms`, `errors`, `spacing`). Библиотеки не нужны: чистый HTML/CSS, тема из `--tg-theme-*` (`core.telegram.org/bots/webapps`).
  - Ресурсы для ассетов (проверить актуальность и лицензии): awesome-telegram-mini-apps (github.com/telegram-mini-apps-dev/awesome-telegram-mini-apps), TelegramUI (React, только для примеров), Lucide, Phosphor, Heroicons, Iconify, LottieFiles, unDraw, Storyset, Unsplash, Mobbin, Dribbble, godly.website. Sketchfab и Poly Haven не нужны для `/mini`.
  - Следующий шаг: по запросу пользователя, новый чат. Редизайн уже в `952ce3f`, открыто: проверить вид в Telegram и вход на адресе туннеля.
  - Готовность к редизайну: сайт на Vercel отвечает, бэкенд тестами покрыт. Перед редизайном `/mini` нужно: проверить вход на адресе туннеля, потом после редизайна пройти сценарий Mini App целиком.
  - Повторная проверка (12.11.2026): чистое venv: `pip check` → «No broken requirements found»; `import multipart, httpx, tzdata, fastapi` OK; маршруты `/` 200, `/login` 200, `/app` 200, `/mini` 200, `/products` без входа 401, `/auth/login-widget` без параметров 400. `uv`/`.venv` pytest → `58 passed, 1 warning`.
- **12.11.2026, /unslop лендинга (режим полировки, по подтверждённому плану)**: `static\css\landing.css`, `templates\landing.html`, `static\js\effects.js`.
  - Сетка шагов переведена на 4 px (8/12/20/32/56/88), межстрочный 1,6, пружина заменена на одну кривую без отскока.
  - Убраны: градиенты (полоска прогресса, финальный блок, аватар чата), свечение и блики под курсором, наклон `.tilt`, подъём карточек и кнопок на hover, пульсация и «!» на хлебе, подёргивание ручек холодильника, курсив и волна под словом «раньше», капс на этикетке, мёртвый CSS (`.card`, `.steps`, `.review`, `.final__tags` и др.).
  - Кнопки: радиус 12 px вместо таблетки. Акцент терракота только у кнопок и штриха в подписях.
  - Первый экран от 900 px: текст слева, холодильник справа.
  - Проверка: `uv run pytest -q` → `58 passed, 1 warning`; в браузере на `127.0.0.1:8000` (1280 px, тёмная тема) вёрстка в две колонки, `.hl` без курсива, пульсации нет. Мобильная ширина и светлая тема не проверены.
  - Не сделано: бегущая строка «made by emeko-emeko …» осталась (ждёт решения пользователя), пробел перед запятой в «раньше , чем» (шаблон), `/mini` и `/login` не трогали.
- **12.11.2026, лендинг: визуал (по подтверждённому плану)**: `templates\landing.html`, `static\css\landing.css`.
  - На левой дверце холодильника бумажная этикетка «Годен до 14.11.2026» со шкалой (те же тексты `label_best_*`, что и в секции «цель»), тень на полу, кант и шов на дверцах. На этикетке в секции «цель» дата оформлена штампом. На телефоне холодильник уже (280 px).
  - Проверка: `uv run pytest -q` → `58 passed, 1 warning`; скриншоты 1280 и 390 px (тёмная тема), этикетка в светлой теме на 390 px. Не смотрел: светлую тему первого экрана на десктопе, секции между первым экраном и финалом, режим с открытой дверцей.

- **12.11.2026, веб-интерфейс `/app` вместо заглушки (по подтверждённому плану, с фото)**:
  - `/app` теперь требует сессию: без cookie `fk_session` редирект 303 на `/login`. Новый `POST /auth/logout` (удаляет сессию и cookie).
  - Новые файлы: `templates\app.html`, `static\css\app.css`, `static\js\app.js`. Удалён `templates\app_placeholder.html`. В `base.html` добавлен `{% block title %}`. В `core\i18n.py` старые ключи `app_text`, `app_back` заменены на `app_*` (шаблон) и `js_app_*` (скрипт), RU и EN.
  - Что умеет: список продуктов по сроку (просрочен / меньше суток / до 3 дней / дальше / без срока), добавление вручную, правка и удаление, распознавание фото через `/products/scan` с кнопками «Да, сохранить» и «Нет, введу сам», выход. Названия вставляются через `textContent`, HTML из названия не выполняется.
  - Проверка: `uv run pytest -q` → `60 passed, 1 warning`. В браузере на временном сервере (SQLite, тестовая сессия, порт 8011): список с цветами статусов, добавление, правка, удаление работают; `<b>Хлеб</b>` показан как текст; на 375 px нет горизонтальной прокрутки, после правки CSS поля даты и названия на всю ширину.
  - Не проверено: распознавание фото на сайте (нужен реальный Yandex Vision и фото), вход через Telegram Login Widget на адресе туннеля, светлая тема, английская версия в браузере (проверена только тестом).
  - Известные ограничения: сессии в памяти (после перезапуска uvicorn вход слетает); копия сайта на Vercel без БД продукты не покажет. `AGENTS.md` не обновлялся, там ещё упомянут `app_placeholder.html`. Не закоммичено.

## Нерешённые вопросы и риски
- Законность обработки данных за пределами Казахстана: решение принято, но юридически не проверено специалистом.
- Словарь продуктов небольшой: продукты вне словаря вводятся вручную.
- ~~Распознавание казахских этикеток: в `ocr.py` указаны только `ru` и `en`~~ — добавлен `kk` (12.11.2026, тесты 58 passed).
- Ссылка «Подключить Telegram» на главной ведёт в бота, а не на `/login`. Это принято, решение о смене отложено.