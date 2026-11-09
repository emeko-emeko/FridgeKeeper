"""Веб-приложение FridgeKeeper: лендинг и заглушка веб-интерфейса."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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


def render(request: Request, template: str, lang: str, save_lang: bool) -> HTMLResponse:
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
    response = templates.TemplateResponse(request, template, context)
    if save_lang:
        response.set_cookie(LANG_COOKIE, lang, max_age=60 * 60 * 24 * 365, path="/", samesite="lax")
    return response


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request) -> HTMLResponse:
    lang, save_lang = resolve_lang(request)
    return render(request, "landing.html", lang, save_lang)


@app.get("/app", response_class=HTMLResponse)
async def app_placeholder(request: Request) -> HTMLResponse:
    lang, save_lang = resolve_lang(request)
    return render(request, "app_placeholder.html", lang, save_lang)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
