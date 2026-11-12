"""Фото этикетки -> текст, название продукта и дата окончания срока годности."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from core.expiry_parser import parse_expiry, parse_expiry_guess
from core.ocr import recognize_text
from core.product_names import find_product_name

# marker — дата рядом с «годен до»; guess — самая поздняя дата без подписи; none — даты нет
Confidence = Literal["marker", "guess", "none"]


@dataclass(frozen=True)
class LabelResult:
    text: str
    product_name: str | None      # предложение из словаря, пользователь может изменить
    expiry_date: date | None      # предложение, пользователь подтверждает
    confidence: Confidence


async def analyze_label(image_bytes: bytes) -> LabelResult:
    text = await recognize_text(image_bytes)
    product_name = find_product_name(text)

    strict = parse_expiry(text)
    if strict is not None:
        return LabelResult(text, product_name, strict, "marker")

    guess = parse_expiry_guess(text)
    if guess is not None:
        return LabelResult(text, product_name, guess, "guess")

    return LabelResult(text, product_name, None, "none")
