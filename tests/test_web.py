from fastapi.testclient import TestClient
import html


from app import app
from core.i18n import TEXTS

client = TestClient(app)


def test_landing_defaults_to_russian():
    response = client.get("/")
    assert response.status_code == 200
    assert '<html lang="ru">' in response.text
    page = html.unescape(response.text)  # Jinja экранирует апострофы и кавычки
    for piece in _hero_pieces("ru"):
        assert piece in page


def test_query_switches_to_english_and_sets_cookie():
    response = client.get("/?lang=en")
    assert response.status_code == 200
    assert '<html lang="en">' in response.text
    page = html.unescape(response.text)
    for piece in _hero_pieces("en"):
        assert piece in page
    assert "lang=en" in response.headers.get("set-cookie", "")


def test_english_page_has_no_cyrillic_outside_language_switch():
    """Английская версия не должна содержать русских слов, кроме переключателя языка."""
    import re

    html = client.get("/?lang=en").text
    html = html.replace(TEXTS["en"]["lang_switch"], "")  # «Русский» в переключателе
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.S)  # скрипты, не текст
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)  # комментарии в шаблонах, не текст
    assert not re.search(r"[А-Яа-яЁё]", html), re.findall(r"[А-Яа-яЁё]+", html)[:5]


def test_russian_page_has_no_english_leftovers_from_hero():
    html = client.get("/").text
    assert "Food Waste at Home" not in html
    assert "Keep track of" not in html


def test_demo_strings_are_passed_to_browser_in_current_language():
    import json
    import re

    en = client.get("/?lang=en").text
    match = re.search(r'<script id="i18n" type="application/json">(.*?)</script>', en, re.S)
    assert match, "JSON строк для скриптов не найден"
    strings = json.loads(match.group(1))
    assert strings["js_count_fmt"] == TEXTS["en"]["js_count_fmt"]
    assert strings["prod_milk"] == "Milk"


def test_cookie_keeps_language_between_requests():
    client.get("/?lang=en")
    response = client.get("/")
    assert '<html lang="en">' in response.text


def test_accept_language_is_used_without_cookie():
    response = TestClient(app).get("/", headers={"accept-language": "en-US,en;q=0.9"})
    assert '<html lang="en">' in response.text


def test_unknown_language_falls_back_to_russian_without_cookie():
    response = TestClient(app).get("/?lang=fr")
    assert '<html lang="ru">' in response.text
    assert "set-cookie" not in response.headers


def test_language_toggle_points_to_other_language():
    ru_page = TestClient(app).get("/").text
    assert 'href="http://testserver/?lang=en"' in ru_page
    en_page = TestClient(app).get("/?lang=en").text
    assert 'href="http://testserver/?lang=ru"' in en_page


def test_app_without_login_redirects_to_login():
    response = TestClient(app).get("/app", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_app_page_renders_in_both_languages_after_login():
    from api.auth import SESSION_COOKIE, make_session_token

    TOKEN_WEB_TEST_TOKEN = make_session_token(1)
    try:
        logged = TestClient(app)
        logged.cookies.set(SESSION_COOKIE, TOKEN_WEB_TEST_TOKEN)
        ru = logged.get("/app?lang=ru")
        en = logged.get("/app?lang=en")
    finally:
        None
    assert ru.status_code == 200 and en.status_code == 200
    assert TEXTS["ru"]["app_title"] in ru.text
    assert TEXTS["en"]["app_title"] in en.text
    assert "/static/js/app.js" in ru.text


def test_logout_clears_cookie():
    from api.auth import SESSION_COOKIE, make_session_token

    logged = TestClient(app)
    logged.cookies.set(SESSION_COOKIE, make_session_token(1))
    response = logged.post("/auth/logout")
    assert response.status_code == 200
    assert f"{SESSION_COOKIE}=" in response.headers.get("set-cookie", "")


def test_static_stylesheet_is_served():
    response = client.get("/static/css/landing.css")
    assert response.status_code == 200
    assert "--accent:" in response.text


def test_both_languages_have_the_same_keys():
    assert set(TEXTS["ru"]) == set(TEXTS["en"])
    for key, value in TEXTS["en"].items():
        assert value.strip(), f"empty English text for {key}"

def _login_button_href(page_html: str) -> str:
    import re
    from urllib.parse import parse_qs, urlsplit

    # Старая кнопка Login Widget: класс tg-login (вторичная кнопка после появления входа через бота)
    match = re.search(r'class="[^"]*tg-login[^"]*" href="([^"]+)"', page_html)
    assert match, "кнопка входа не найдена"
    return html.unescape(match.group(1))


def test_login_on_vercel_host_uses_login_widget(monkeypatch):
    import app as app_module
    from urllib.parse import parse_qs, urlsplit

    monkeypatch.setattr(app_module, "PUBLIC_BASE_URL", "")
    response = TestClient(app).get("/login", headers={"host": "fridge-keeper-eight.vercel.app"})
    assert response.status_code == 200
    href = _login_button_href(response.text)
    assert href.startswith("https://oauth.telegram.org/auth?")
    query = parse_qs(urlsplit(href).query)
    assert query["origin"][0].endswith("fridge-keeper-eight.vercel.app")
    assert query["return_to"][0].endswith("fridge-keeper-eight.vercel.app/auth/login-widget")


def test_login_with_public_base_url_returns_to_it(monkeypatch):
    import app as app_module
    from urllib.parse import parse_qs, urlsplit

    public = "https://example-tunnel.trycloudflare.com"
    monkeypatch.setattr(app_module, "PUBLIC_BASE_URL", public)
    response = TestClient(app).get("/login", headers={"host": "fridge-keeper-eight.vercel.app"})
    href = _login_button_href(response.text)
    assert href.startswith("https://oauth.telegram.org/auth?")
    query = parse_qs(urlsplit(href).query)
    assert query["origin"] == [public]
    assert query["return_to"][0].startswith(public + "/auth/login-widget")


def _hero_pieces(lang: str) -> list[str]:
    t = TEXTS[lang]
    return [t["hero_title_pre"], t["hero_title_hl"], t["hero_title_post"]]

