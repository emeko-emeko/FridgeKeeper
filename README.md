# FridgeKeeper

Пет-проект для контроля сроков годности продуктов. Позволяет закидывать фото этикеток, распознавать даты с помощью OCR, вести учет запасов в холодильнике и получать напоминания в Telegram до того, как еда испортится.

## Что умеет

- **Сканирование этикеток:** отправка фото с упаковкой, распознавание текста через Yandex Vision API и автоматическое вытягивание названия и даты («Годен до»).
- **Уведомления в Telegram:** бот присылает пуш за пару дней до окончания срока годности.
- **Связка веб-сессии и бота:** можно пользоваться сайтом без регистрации, а потом привязать Telegram через одноразовый токен (`/start <token>`).
- **Подсказки по хранению:** базовый справочник по товарному соседству и оптимальной температуре для разных категорий еды.

## Стек

- **Backend:** Python 3.10+, Flask / FastAPI, SQLAlchemy
- **Telegram Bot:** `aiogram`
- **OCR:** Yandex Vision API
- **Database:** SQLite (`instance/fridge.db`)
- **Frontend:** HTML, Tailwind CSS, JS (Fetch / Web Cam API)

## Структура проекта

```text
fridge-keeper/
├── bot/            # Хэндлеры и логика Telegram-бота
├── core/           # Конфиг и подключение к БД
├── instance/       # Файлы локальной БД SQLite
├── models/         # SQLAlchemy модели (User, Product)
├── services/       # OCR, парсинг дат, сервисы уведомлений
├── .env            # Переменные окружения (в .gitignore)
├── app.py          # Запуск веб-приложения
└── README.md
```

## Быстрый старт

### 1. Клонирование и виртуальное окружение

```bash
git clone https://github.com/your-username/fridge-keeper.git
cd fridge-keeper

python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

### 2. Зависимости и переменные окружения

Установите библиотеки:
```bash
pip install -r requirements.txt
```

Создайте `.env` в корне:
```ini
TELEGRAM_TOKEN=ваш_токен_бота
YANDEX_API_KEY=ваш_api_key
YANDEX_FOLDER_ID=ваш_folder_id
DATABASE_URL=sqlite:///instance/fridge.db
SECRET_KEY=секретный_ключ_сессии
```

### 3. Запуск

Запуск бэкенда:
```bash
python app.py
```

Запуск Telegram-бота (в отдельном терминале):
```bash
python -m bot.main
```

## Как устроена связка Web -> Telegram

1. При открытии сайта для гостя создается анонимный пользователь в БД (`telegram_id = NULL`).
2. При клике на «Подключить Telegram» сайт выдает ссылку вида `https://t.me/FridgeKeeper_MESSAGE_BOT?start=<token>`.
3. При переходе в бота команда `/start` считывает токен и прописывает `telegram_id` в запись этого пользователя.
4. Все товары, добавленные через веб-интерфейс, начинают отслеживаться ботом.