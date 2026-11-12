"""Проверка распознавания этикетки без сайта и без Mini App.

Запуск из папки проекта:
    uv run python scripts/check_ocr.py test.png
"""

import asyncio
import sys
from datetime import date
from pathlib import Path

# Чтобы импорт core.* работал при запуске из папки scripts
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.label_service import analyze_label  # noqa: E402
from core.ocr import OcrError  # noqa: E402


async def main() -> None:
    if len(sys.argv) < 2:
        print("Укажите файл: python scripts/check_ocr.py путь/к/фото.jpg")
        return

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Файл не найден: {path}")
        return

    try:
        result = await analyze_label(path.read_bytes())
    except OcrError as err:
        print(f"Ошибка OCR: {err}")
        return

    print("--- распознанный текст ---")
    print(result.text or "(пусто)")
    print("--- предложенное название ---")
    print(result.product_name or "не найдено, введите вручную")
    print("--- найденная дата ---")
    if result.expiry_date is None:
        print("не найдена")
    else:
        note = {
            "marker": "рядом с подписью «годен до»",
            "guess": "предположение: самая поздняя дата без подписи, нужно подтвердить",
        }.get(result.confidence, "")
        print(f"{result.expiry_date} ({note})")
        if result.expiry_date < date.today():
            print("ВНИМАНИЕ: срок уже истёк")


if __name__ == "__main__":
    # Консоль Windows (cp1251) не печатает казахские буквы, поэтому выводим в UTF-8
    sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
