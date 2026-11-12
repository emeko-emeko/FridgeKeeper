"""Распознавание текста на этикетке через Yandex Vision. Фото не сохраняется на диск."""

import base64

import httpx

from core.config import YANDEX_API_KEY, YANDEX_FOLDER_ID

VISION_URL = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"


class OcrError(Exception):
    """Не удалось распознать изображение (нет ключей, сеть, ошибка API)."""


async def recognize_text(image_bytes: bytes, timeout: float = 20.0) -> str:
    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        raise OcrError("Не заданы YANDEX_API_KEY или YANDEX_FOLDER_ID")

    payload = {
        "folderId": YANDEX_FOLDER_ID,
        "analyze_specs": [{
            "content": base64.b64encode(image_bytes).decode("utf-8"),
            "features": [{
                "type": "TEXT_DETECTION",
                "text_detection_config": {"language_codes": ["ru", "en", "kk"]},
            }],
        }],
    }
    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(VISION_URL, headers=headers, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as err:
        raise OcrError(f"Ошибка запроса к Yandex Vision: {err}") from err

    return _extract_lines(response.json())


def _extract_lines(data: dict) -> str:
    """Собирает строки текста из ответа Vision. Пустой список — не ошибка, а пустой результат."""
    lines: list[str] = []
    try:
        text_detection = data["results"][0]["results"][0]["textDetection"]
    except (KeyError, IndexError, TypeError):
        return ""

    for page in text_detection.get("pages", []):
        for block in page.get("blocks", []):
            for line in block.get("lines", []):
                words = [word.get("text", "") for word in line.get("words", [])]
                lines.append(" ".join(words))
    return "\n".join(lines)