# FridgeKeeper

Сервис контроля сроков годности продуктов. Фото этикетки или ручной ввод, список продуктов по срокам и напоминания в Telegram за 24, 12, 6 и 2 часа до истечения срока.

Состоит из трёх входов к одному ядру:

- **Telegram-бот** `@FridgeKeeper_MESSAGE_BOT`: команды и фото этикеток.
- **Сайт**: лендинг на русском и английском, вход через Telegram, список продуктов на `/app`.
- **Mini App** `/mini`: страница внутри Telegram с камерой для добавления продукта по фото.

Фото этикеток не сохраняются: они читаются в памяти и отправляются на распознавание.

## Возможности

### Бот

| Команда | Что делает |
|---|---|
| `/start` | Регистрация. С токеном (`/start <token>`) связывает бот с аккаунтом на сайте |
| `/help` | Список команд |
| `/my_products` | Все продукты и сроки годности |
| `/add Название; ДД.ММ.ГГГГ` | Добавить продукт. Дату можно не указывать |
| `/soon` | Что истекает в ближайшие 3 дня, включая уже просроченное |
| `/delete Название` | Удалить продукт, если совпадение одно |

Фото этикетки бот распознаёт, показывает название и дату и просит подтвердить кнопками «Да, сохранить» или «Нет, введу сам».

### Сайт

- `/` — лендинг (RU/EN).
- `/login` — вход через Telegram Login Widget. После входа выдаётся подписанная cookie `fk_session`.
- `/app` — список продуктов по срокам, добавление, правка, удаление, добавление по фото. Без входа перенаправляет на `/login`.
- `/mini` — страница Mini App. Вход через `initData` Telegram, токен хранится только в памяти страницы.

### Правила

- **Дедлайн** — 00:00 дня, следующего за датой на этикетке. «Годен до 12.05» → дедлайн 13.05 00:00 (часовой пояс Asia/Almaty).
- **Уведомления** — один раз на каждый уровень (24, 12, 6, 2 часа). Если уровни пропущены, например бот был выключен, приходит одно сообщение о самом срочном, остальные помечаются как пропущенные.
- **Дата без подписи «годен до»** — берётся самая поздняя дата на этикетке и помечается как предположение.
- **Просроченный продукт** — показывается с предупреждением. Сохранить можно после подтверждения.
- **Название** — сопоставляется со словарём `KNOWN_PRODUCTS` (`core/product_names.py`). Продукты вне словаря вводятся вручную.

## Стек

- Python 3.12+
- FastAPI + Jinja2 (сайт, API, Mini App)
- aiogram 3 (бот)
- SQLAlchemy 2 (async) + Alembic (миграции)
- APScheduler (напоминания, проверка каждые 5 минут, работает в процессе бота)
- Yandex Vision OCR (распознавание текста на этикетке)
- PostgreSQL (Neon) в продакшене, SQLite для локальных экспериментов
- GSAP и Lenis на лендинге (файлы в `static/vendor/`)

## Структура проекта

```text
FridgeKeeper/
├── app.py              # FastAPI: маршруты /, /login, /app, /mini, подключение API
├── api/
│   ├── auth.py         # /auth/login-widget, /auth/mini-app, /auth/me, /auth/logout
│   └── products.py     # /products/scan, /products (GET, POST, PATCH, DELETE)
├── bot/
│   ├── main.py         # точка входа бота, меню команд, запуск планировщика
│   ├── handlers.py     # команды и фото
│   └── formatting.py   # тексты сообщений бота
├── core/
│   ├── config.py       # настройки из .env, нормализация строки PostgreSQL
│   ├── database.py     # движок и фабрика сессий
│   ├── ocr.py          # запрос к Yandex Vision
│   ├── label_service.py# распознавание этикетки: текст, название, дата
│   ├── expiry_parser.py# разбор дат на этикетке
│   ├── product_names.py# словарь известных продуктов
│   ├── notifications.py# дедлайны и уровни напоминаний
│   ├── scheduler.py    # APScheduler, отправка напоминаний через бота
│   ├── linking.py      # одноразовые токены связки сайт ↔ Telegram
│   ├── telegram_auth.py# проверка подписи Login Widget и initData
│   ├── products.py     # выборки продуктов
│   ├── users.py        # пользователи
│   └── i18n.py         # все тексты сайта на RU и EN
├── models/             # User, Product, LinkToken, NotificationLog
├── migrations/         # Alembic, версии схемы
├── templates/          # landing, login, app, mini, base
├── static/             # css, js, изображения, vendor
├── scripts/
│   ├── check_ocr.py    # проверка OCR на фото без сайта
│   └── migrate_sqlite_to_pg.py  # перенос данных из SQLite в PostgreSQL
├── tests/              # pytest
├── requirements.txt    # зависимости для Vercel и pip
├── pyproject.toml      # зависимости для uv (его читает Vercel тоже)
└── alembic.ini
```

## Переменные окружения

Файл `.env` в корне проекта (в git не попадает). Значения здесь не приводятся.

| Переменная | Нужна | Назначение |
|---|---|---|
| `TELEGRAM_TOKEN` | да | Токен бота от @BotFather |
| `YANDEX_API_KEY` | да | Ключ Yandex Cloud для Vision OCR |
| `YANDEX_FOLDER_ID` | да | ID каталога Yandex Cloud |
| `DATABASE_URL` | да | Строка подключения. Для PostgreSQL можно `postgresql://…` или `postgres://…`, драйвер подставится сам |
| `SESSION_SECRET` | да в продакшене | Ключ подписи сессий сайта. Без него сессии слетают при каждом перезапуске |
| `TEST_DATABASE_URL` | для тестов | Строка подключения к тестовой базе |
| `PUBLIC_BASE_URL` | нет | Публичный адрес сайта, если он отличается от адреса запроса (например, туннель) |
| `LINK_TOKEN_TTL_MINUTES` | нет | Срок жизни токена связки, по умолчанию 10 минут |

Если `DATABASE_URL` не задан, используется `instance/database.db` (SQLite).

## Быстрый старт

Нужны Python 3.12+ и [uv](https://docs.astral.sh/uv/) (или `pip`).

### 1. Зависимости

```bash
uv sync
```

Без uv:

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

### 2. Файл `.env`

Создайте `.env` в корне по таблице выше.

### 3. Миграции

```bash
uv run alembic upgrade head
```

Схему создаёт только Alembic. Бот и сайт таблицы сами не создают.

### 4. Сайт

```bash
uv run uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Открыть: `http://127.0.0.1:8000`.

### 5. Бот

В отдельном терминале:

```bash
uv run python -m bot.main
```

Бот при старте выставляет меню команд и запускает планировщик напоминаний.

## Что нужно настроить для входа и Mini App

- **Вход через Telegram** работает только на домене, который привязан к боту. В @BotFather выполните `/setdomain` и укажите домен сайта. Адрес `127.0.0.1` и `localhost` не подходят.
- **Mini App** открывается из Telegram только по HTTPS-адресу. Для локальной разработки используйте туннель (например, `cloudflared tunnel --url http://127.0.0.1:8000`) и укажите его в @BotFather через `/newapp` или `/setdomain`. Адрес туннеля меняется при каждом запуске.
- Запуск за туннелем: `uv run uvicorn app:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips="*"`.

## Тесты

```bash
uv run pytest
```

Тесты читают `TEST_DATABASE_URL` из `.env`. Для быстрого прогона без PostgreSQL можно указать SQLite:

```bash
TEST_DATABASE_URL="sqlite+aiosqlite:///./test.db" uv run pytest -q
```

Если `pytest-asyncio` не установлен, добавьте его: `uv pip install pytest-asyncio`. В `pyproject.toml` его пока нет, а `requirements.txt` содержит.

Последний прогон: 67 тестов, все прошли (на SQLite).

## Развёртывание на Vercel

Сайт задеплоен на Vercel: `https://fridge-keeper-eight.vercel.app`. Vercel ставит зависимости из `pyproject.toml`, поэтому при добавлении пакета обновляйте и `pyproject.toml`, и `requirements.txt`.

Переменные в проекте Vercel: `DATABASE_URL` (Neon), `SESSION_SECRET`, `TELEGRAM_TOKEN`, `YANDEX_API_KEY`, `YANDEX_FOLDER_ID`.

Миграции на Neon запускаются вручную с тем же `DATABASE_URL`:

```bash
uv run alembic upgrade head
```

## Маршруты

| Метод и путь | Доступ | Что делает |
|---|---|---|
| `GET /` | всем | Лендинг |
| `GET /login` | всем | Страница входа через Telegram |
| `GET /auth/login-widget` | подпись Telegram | Завершает вход, ставит cookie `fk_session` |
| `GET /app` | сессия | Веб-интерфейс списка продуктов |
| `GET /mini` | всем (данные за токеном) | Страница Mini App |
| `POST /auth/mini-app` | `initData` | Выдаёт токен Mini App |
| `GET /auth/me` | токен или cookie | Текущий пользователь |
| `POST /auth/logout` | сессия | Сбрасывает cookie |
| `POST /products/scan` | сессия | Распознаёт фото этикетки, ничего не сохраняет |
| `GET /products` | сессия | Список продуктов |
| `POST /products` | сессия | Сохраняет продукт (`expiry_source`: `ocr`, `manual` или `bot`) |
| `PATCH /products/{id}` | сессия | Меняет название или срок (`null` убирает срок) |
| `DELETE /products/{id}` | сессия | Удаляет продукт |

Чужой продукт возвращает 404.

## Скрипты

- `uv run python scripts/check_ocr.py путь/к/фото.png` — проверка распознавания этикетки без сайта и бота.
- `scripts/migrate_sqlite_to_pg.py` — одноразовый перенос данных из SQLite в PostgreSQL.

## Известные ограничения

- Словарь продуктов небольшой. Остальное вводится вручную.
- Распознавание и хостинг сайта используют сервисы за пределами Казахстана (Yandex Vision, Vercel). Это принятое решение проекта.
- Напоминания отправляет процесс бота. Если бот не запущен, напоминания не уходят. Пропущенные уровни догоняются одним сообщением при следующем запуске.
- Пользователь получает напоминания только после `/start` в боте. Сайт показывает об этом напоминание.
- Сессия сайта действует 30 дней. Выход удаляет cookie в браузере, но сам токен на сервере не отзывается до истечения срока.
