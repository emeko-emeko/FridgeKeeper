import sqlite3

# Подключаемся к одному файлу базы данных
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# 1. Создаем таблицу пользователей
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id BIGINT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""
)

# 2. Создаем таблицу продуктов в том же файле
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        category TEXT,
        expiry_date DATE,
        storage_advice TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
"""
)

conn.commit()
conn.close()