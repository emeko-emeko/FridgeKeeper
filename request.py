import base64
import os
import requests
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
VISION_URL = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"


def recognize_label_image(image_path: str) -> str:
  """Отправляет изображение этикетки в Yandex Vision API

  и возвращает распознанный текст.
  """
  if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
    raise ValueError(
        "Отсутствуют ключи YANDEX_API_KEY или YANDEX_FOLDER_ID в файле .env"
    )

  # 1. Читаем файл изображения и переводим в Base64
  if not os.path.exists(image_path):
    raise FileNotFoundError(f"Файл изображения не найден: {image_path}")

  with open(image_path, "rb") as f:
    image_bytes = f.read()
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

  # 2. Формируем заголовки и тело запроса
  headers = {
      "Content-Type": "application/json",
      "Authorization": f"Api-Key {YANDEX_API_KEY}",
  }

  payload = {
      "folderId": YANDEX_FOLDER_ID,
      "analyze_specs": [{
          "content": encoded_image,
          "features": [{
              "type": "TEXT_DETECTION",
              "text_detection_config": {"language_codes": ["ru", "en"]},
          }],
      }],
  }

  # 3. Отправляем POST-запрос к Yandex Vision
  try:
    response = requests.post(VISION_URL, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()

    # 4. Извлекаем текст из ответа API
    extracted_lines = []
    results = (
        result.get("results", [{}])[0].get("results", [{}])[0].get("textDetection", {})
    )
    for page in results.get("pages", []):
      for block in page.get("blocks", []):
        for line in block.get("lines", []):
          line_text = " ".join(
              [word.get("text", "") for word in line.get("words", [])]
          )
          extracted_lines.append(line_text)

    return "\n".join(extracted_lines)

  except requests.exceptions.HTTPError as http_err:
    print(
        f"Ошибка HTTP при запросе к Yandex Vision: {http_err} | Ответ:"
        f" {response.text}"
    )
    return ""
  except Exception as err:
    print(f"Произошла ошибка при обработке изображения: {err}")
    return ""


# --- Пример локального запуска для проверки ---
if __name__ == "__main__":
  # Укажите путь к тестовой картинке с этикеткой
  test_image = "test_label.jpg"

  print(f"Отправка файла {test_image} в Yandex Vision...")
  text = recognize_label_image(test_image)

  print("\n--- Распознанный текст ---")
  print(text if text else "Текст не найден или произошла ошибка.")