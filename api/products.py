"""Продукты: распознавание фото этикетки, сохранение подтверждённого продукта, список.

Фото читается в памяти и не сохраняется на диск.
"""

from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import current_user_id
from core.database import SessionFactory
from core.label_service import analyze_label
from core.notifications import TZ
from core.ocr import OcrError
from core.products import list_user_products
from models import Product

router = APIRouter(prefix="/products")

MAX_PHOTO_BYTES = 10 * 1024 * 1024  # 10 МБ


def _used_at_json(product: Product) -> str | None:
    return product.used_at.isoformat() if product.used_at else None


async def get_session() -> AsyncSession:
    async with SessionFactory() as session:
        yield session


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    expiry_date: date | None = None
    # "ocr" — пользователь принял предложенную дату, "manual" — ввёл или изменил сам
    expiry_source: Literal["ocr", "manual", "bot"] = "manual"


@router.post("/scan")
async def scan_label(
    file: UploadFile = File(...),
    user_id: int = Depends(current_user_id),
):
    """Распознаёт фото и возвращает предложения. Ничего не сохраняет."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Пустой файл")
    if len(data) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="Фото больше 10 МБ")

    try:
        result = await analyze_label(data)
    except OcrError as err:
        raise HTTPException(status_code=502, detail=str(err)) from err

    today = datetime.now(TZ).date()
    expired = result.expiry_date is not None and result.expiry_date < today
    return {
        "product_name": result.product_name,
        "expiry_date": result.expiry_date.isoformat() if result.expiry_date else None,
        "confidence": result.confidence,
        "expired": expired,
    }


@router.post("", status_code=201)
async def create_product(
    body: ProductCreate,
    user_id: int = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Сохраняет продукт, который пользователь подтвердил. Просроченный продукт тоже можно сохранить."""
    product = Product(
        user_id=user_id,
        name=body.name.strip(),
        expiry_date=body.expiry_date,
        expiry_source=body.expiry_source,
    )
    session.add(product)
    await session.commit()
    return {
        "id": product.id,
        "name": product.name,
        "expiry_date": product.expiry_date.isoformat() if product.expiry_date else None,
        "expiry_source": product.expiry_source,
        "used_at": _used_at_json(product),
    }


@router.get("")
async def list_products(
    user_id: int = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    products = await list_user_products(session, user_id)
    return [
        {
            "id": p.id,
            "name": p.name,
            "expiry_date": p.expiry_date.isoformat() if p.expiry_date else None,
            "used_at": _used_at_json(p),
        }
        for p in products
    ]


class ProductUpdate(BaseModel):
    """Поля необязательны. expiry_date = null означает «убрать срок»."""

    name: str | None = Field(default=None, max_length=100)
    expiry_date: date | None = None
    expiry_source: Literal["ocr", "manual", "bot"] | None = None
    # true — отметить «Использовано» (время ставится, если его ещё нет), false — снять отметку
    used: bool | None = None


async def _own_product(session: AsyncSession, user_id: int, product_id: int) -> Product:
    """Чужой или несуществующий продукт — один и тот же ответ 404, чтобы не показывать чужие id."""
    product = await session.get(Product, product_id)
    if product is None or product.user_id != user_id:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    return product


@router.patch("/{product_id}")
async def update_product(
    product_id: int,
    body: ProductUpdate,
    user_id: int = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    product = await _own_product(session, user_id, product_id)

    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=422, detail="Название не может быть пустым")
        product.name = name
    if "expiry_date" in body.model_fields_set:
        product.expiry_date = body.expiry_date
        product.expiry_source = body.expiry_source or "manual"
    elif body.expiry_source is not None:
        product.expiry_source = body.expiry_source

    if body.used is True and product.used_at is None:
        product.used_at = datetime.now(UTC)
    elif body.used is False:
        product.used_at = None

    await session.commit()
    return {
        "id": product.id,
        "name": product.name,
        "expiry_date": product.expiry_date.isoformat() if product.expiry_date else None,
        "expiry_source": product.expiry_source,
        "used_at": _used_at_json(product),
    }


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    user_id: int = Depends(current_user_id),
    session: AsyncSession = Depends(get_session),
):
    product = await _own_product(session, user_id, product_id)
    await session.delete(product)
    await session.commit()
    return Response(status_code=204)
