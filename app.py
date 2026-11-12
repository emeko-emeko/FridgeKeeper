"""Веб-приложение FridgeKeeper: лендинг, вход и веб-интерфейс продуктов."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.auth import SESSION_COOKIE, read_session_token
from core.config import TELEGRAM_TOKEN
from api.auth import router as auth_router
from api.products import router as products_router
from core.i18n import (
    APP_URL,
    DEFAULT_LANG,
    TELEGRAM_BOT_URL,
    get_js_strings,
    get_texts,
    normalize_lang,
)

BASE_DIR = Path(__file__).resolve().parent
LANG_COOKIE = "lang"

app = FastAPI(title="FridgeKeeper", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://fridge-keeper-eight.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router)
app.include_router(products_router)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def resolve_lang(request: Request) -> tuple[str, bool]:
    """Определить язык.

    Приоритет: параметр ?lang=, затем cookie, затем заголовок Accept-Language.
    Второй элемент — нужно ли сохранить выбор в cookie (True, если язык задан явно).
    """
    explicit = normalize_lang(request.query_params.get("lang"))
    if explicit:
        return explicit, True

    from_cookie = normalize_lang(request.cookies.get(LANG_COOKIE))
    if from_cookie:
        return from_cookie, False

    accept = request.headers.get("accept-language", "").lower()
    if accept.startswith("en"):
        return "en", False
    return DEFAULT_LANG, False


def render(
    request: Request,
    template: str,
    lang: str,
    save_lang: bool,
    extra: dict | None = None,
) -> HTMLResponse:
    # JSON для скриптов демо; "<" экранируем, чтобы строки не закрыли тег <script>.
    js_json = json.dumps(get_js_strings(lang), ensure_ascii=False).replace("<", "\\u003c")
    context = {
        "t": get_texts(lang),
        "js_json": js_json,
        "lang": lang,
        "other_lang": "en" if lang == "ru" else "ru",
        "app_url": APP_URL,
        "bot_url": TELEGRAM_BOT_URL,
    }
    if extra:
        context.update(extra)
    response = templates.TemplateResponse(request, template, context)
    if save_lang:
        response.set_cookie(LANG_COOKIE, lang, max_age=60 * 60 * 24 * 365, path="/", samesite="lax")
    return response


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request) -> HTMLResponse:
    lang, save_lang = resolve_lang(request)
    return render(request, "landing.html", lang, save_lang)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    """Страница входа с Telegram Login Widget.

    Адрес возврата строится от текущего адреса сайта. За туннелем это https://…trycloudflare.com,
    поэтому запускать uvicorn нужно с --proxy-headers (см. инструкцию).
    """
    lang, save_lang = resolve_lang(request)
    auth_url = str(request.base_url).rstrip("/") + "/auth/login-widget"
    # Кнопка ведёт на страницу входа Telegram; она вернёт пользователя на auth_url с подписью.
    origin = str(request.base_url).rstrip("/")
    bot_id = TELEGRAM_TOKEN.split(":")[0] if TELEGRAM_TOKEN else ""
    telegram_url = "https://oauth.telegram.org/auth?" + urlencode(
        {"bot_id": bot_id, "origin": origin, "request_access": "write", "return_to": auth_url}
    )
    return render(request, "login.html", lang, save_lang, {"auth_url": auth_url, "telegram_url": telegram_url})


@app.get("/app", response_class=HTMLResponse)
async def web_app(request: Request):
    """Веб-интерфейс списка продуктов. Без сессии отправляем на вход."""
    if read_session_token(request.cookies.get(SESSION_COOKIE)) is None:
        return RedirectResponse(url="/login", status_code=303)
    lang, save_lang = resolve_lang(request)
    return render(request, "app.html", lang, save_lang)


@app.get("/mini", response_class=HTMLResponse)
async def mini_app(request: Request) -> HTMLResponse:
    """Страница Mini App. Отдаётся с ПК через туннель, поэтому CORS не нужен."""
    return templates.TemplateResponse(request, "mini.html", {})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
