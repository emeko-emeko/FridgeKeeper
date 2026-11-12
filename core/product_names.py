"""Поиск названия продукта в тексте этикетки по словарю.

Текст от OCR может быть на латинице и с диакритикой («ÍOGURT» -> «iogurt»),
поэтому сравниваем нормализованные слова: без регистра, без акцентов, с общим написанием.
Результат — предложение названия. Пользователь может его поменять.
"""

import re
import unicodedata

# Каноническое название (показываем пользователю) -> возможные написания на этикетке
KNOWN_PRODUCTS: dict[str, tuple[str, ...]] = {
    "Йогурт": ("йогурт", "yogurt", "yoghurt", "iogurt"),
    "Кефир": ("кефир", "kefir"),
    "Молоко": ("молоко", "milk", "moloko"),
    "Сыр": ("сыр", "сыры", "cheese", "syr"),
    "Творог": ("творог", "cottage", "tvorog"),
    "Сметана": ("сметана", "smetana", "sour cream"),
    "Масло сливочное": ("масло", "butter", "maslo"),
    "Хлеб": ("хлеб", "bread", "hleb", "khleb"),
    "Яйца": ("яйца", "яйцо", "eggs", "egg", "yaytsa"),
    "Колбаса": ("колбаса", "sausage", "kolbasa"),
    "Сок": ("сок", "juice", "sok"),
    "Огурцы": ("огурцы", "огурец", "cucumber", "cucumbers", "ogurtsy"),
    "Помидоры": ("помидоры", "помидор", "tomato", "tomatoes", "pomidory"),
    "Брокколи": ("брокколи", "broccoli"),
    "Варенье": ("варенье", "jam"),
    "Майонез": ("майонез", "mayonnaise", "mayo"),
    "Кетчуп": ("кетчуп", "ketchup"),
}

_WORD_RE = re.compile(r"[a-zа-яё]+")


def _normalize(text: str) -> str:
    """Нижний регистр, ё->е, без акцентов: «ÍOGURT» -> «iogurt», «Нәтіге» -> «нэтиге»."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return without_marks.replace("ё", "е")


def _variant_matches(token: str, variant: str) -> bool:
    """Точное совпадение слова, либо совпадение начала для длинных слов (падежи, множественное число)."""
    variant = _normalize(variant)
    if " " in variant:
        return variant in token
    if token == variant:
        return True
    return len(variant) >= 4 and token.startswith(variant)


def find_product_name(text: str) -> str | None:
    """Первый продукт из словаря, встреченный в тексте (по порядку следования слов)."""
    tokens = _WORD_RE.findall(_normalize(text))
    for token in tokens:
        for canonical, variants in KNOWN_PRODUCTS.items():
            if any(_variant_matches(token, v) for v in variants):
                return canonical
    return None
