"""Вход на сайт: Login Widget (браузер) и Mini App (внутри Telegram)."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import SessionFactory
from core.telegram_auth import TelegramAuthError, verify_login_widget, verify_mini_app
from core.users import get_or_create_user
from models import LinkToken  # noqa: F401 — модели регистрируются через models

router = APIRouter(prefix="/auth")

SESSION_COOKIE = "fk_session"
# Сессии в памяти: достаточно для одного ПК. Потом перенесём в БД или Redis.
SESSIONS: dict[str, int] = {}  # токен -> user_id


async def get_session() -> AsyncSession:
    async with SessionFactory() as session:
        yield session


@router.get("/login-widget")
async def login_widget_callback(request: Request, session: AsyncSession = Depends(get_session)):
    """Telegram Login Widget перенаправляет сюда с параметрами пользователя."""
    fields = dict(request.query_params)
    try:
        telegram_id = verify_login_widget(fields)
    except (TelegramAuthError, KeyError, ValueError) as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    user = await get_or_create_user(session, telegram_id)
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = user.id

    response = RedirectResponse(url="/app", status_code=303)
    response.set_cookie(
        SESSION_COOKIE, token, httponly=True, secure=True, samesite="lax", max_age=30 * 24 * 3600
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
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = user.id
    return {"ok": True, "token": token}


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
    if not token or token not in SESSIONS:
        raise HTTPException(status_code=401, detail="Нужен вход")
    return SESSIONS[token]


@router.get("/me")
async def me(user_id: int = Depends(current_user_id)):
    """Проверка сессии: возвращает id пользователя по токену или cookie."""
    return {"user_id": user_id}
