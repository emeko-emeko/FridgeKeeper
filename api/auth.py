"""Вход на сайт: Login Widget (браузер) и Mini App (внутри Telegram)."""

import base64
import hashlib
import hmac
import json
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import SESSION_SECRET
from core.database import SessionFactory
from core.telegram_auth import TelegramAuthError, verify_login_widget, verify_mini_app
from core.users import get_or_create_user
from models import LinkToken  # noqa: F401 — модели регистрируются через models

router = APIRouter(prefix="/auth")

SESSION_COOKIE = "fk_session"
SESSION_TTL_SECONDS = 30 * 24 * 3600
LOGIN_BRIDGE_PATH = Path(__file__).resolve().parent.parent / "templates" / "login_bridge.html"


def make_session_token(user_id: int, now: float | None = None) -> str:
    """Подписанный токен: payload.подпись. Не хранится на сервере, поэтому работает на любом инстансе."""
    exp = int((now if now is not None else time.time()) + SESSION_TTL_SECONDS)
    payload = base64.urlsafe_b64encode(json.dumps({"uid": user_id, "exp": exp}).encode()).decode()
    sig = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def read_session_token(token: str | None, now: float | None = None) -> int | None:
    """Возвращает user_id, если подпись верна и срок не истёк, иначе None."""
    if not token or "." not in token:
        return None
    payload, _, sig = token.rpartition(".")
    expected = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(payload.encode()))
    except (ValueError, TypeError):
        return None
    current = now if now is not None else time.time()
    if not isinstance(data.get("uid"), int) or data.get("exp", 0) < current:
        return None
    return data["uid"]


async def get_session() -> AsyncSession:
    async with SessionFactory() as session:
        yield session


@router.get("/login-widget")
async def login_widget_callback(request: Request, session: AsyncSession = Depends(get_session)):
    """Telegram Login Widget перенаправляет сюда с параметрами пользователя.

    Новый вариант Telegram отдаёт данные во фрагменте адреса (#tgAuthResult=…), который сервер не видит.
    Без параметра hash отдаём страницу-мост: она переносит данные в параметры и вызывает этот же адрес.
    """
    if "hash" not in request.query_params:
        return HTMLResponse(
            LOGIN_BRIDGE_PATH.read_text(encoding="utf-8"),
            headers={"Cache-Control": "no-store"},
        )
    fields = dict(request.query_params)
    try:
        telegram_id = verify_login_widget(fields)
    except (TelegramAuthError, KeyError, ValueError) as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    user = await get_or_create_user(session, telegram_id)
    token = make_session_token(user.id)

    response = RedirectResponse(url="/app", status_code=303)
    response.set_cookie(
        SESSION_COOKIE, token, httponly=True, secure=True, samesite="lax", max_age=SESSION_TTL_SECONDS
    )
    return response


class MiniAppAuth(BaseModel):
    init_data: str


@router.post("/mini-app")
async def mini_app_auth(body: MiniAppAuth, session: AsyncSession = Depends(get_session)):
    """Mini App передаёт initData; проверяем подпись и возвращаем токен сессии.

    Токен отдаём в JSON, а не в cookie: cookie с Vercel на туннель в Firefox,
    Safari и во встроенном браузере Telegram часто блокируется.
    """
    try:
        telegram_id = verify_mini_app(body.init_data)
    except TelegramAuthError as err:
        raise HTTPException(status_code=401, detail=str(err)) from err

    user = await get_or_create_user(session, telegram_id)
    return {"ok": True, "token": make_session_token(user.id)}


def current_user_id(request: Request) -> int:
    """Зависимость для защищённых эндпоинтов.

    Сначала ищет заголовок Authorization: Bearer <token> (Mini App),
    затем cookie (вход через браузер).
    """
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        token = header[7:].strip()
    else:
        token = request.cookies.get(SESSION_COOKIE)
    user_id = read_session_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Нужен вход")
    return user_id


@router.post("/logout")
async def logout(request: Request):
    """Сбрасывает cookie. Токен без серверного состояния, истекает сам через SESSION_TTL_SECONDS."""
    response = JSONResponse({"ok": True})
    response.delete_cookie(SESSION_COOKIE)
    return response


@router.get("/me")
async def me(user_id: int = Depends(current_user_id)):
    """Проверка сессии: возвращает id пользователя по токену или cookie."""
    return {"user_id": user_id}
