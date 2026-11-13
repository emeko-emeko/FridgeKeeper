/* Вход по коду из бота: человек открывает бота, получает код XXXX-XXXX и вводит его здесь.
   Cookie ставит сервер, мы только переходим на /app. */
(function () {
  "use strict";

  var T = {};
  try { T = JSON.parse(document.getElementById("i18n").textContent); } catch (e) {}
  function tr(key) { return T["js_login_" + key] || key; }

  var form = document.getElementById("code-form");
  var input = document.getElementById("code-input");
  var submit = document.getElementById("code-submit");
  var msg = document.getElementById("login-msg");
  if (!form || !input || !submit || !msg) return;

  var busy = false;

  function say(text) {
    msg.hidden = !text;
    msg.textContent = text || "";
    input.setAttribute("aria-invalid", text ? "true" : "false");
  }

  // Только буквы и цифры, верхний регистр, максимум 8 символов, дефис после четвёртого.
  function clean(value) {
    return value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8);
  }
  function pretty(raw) {
    return raw.length > 4 ? raw.slice(0, 4) + "-" + raw.slice(4) : raw;
  }

  input.addEventListener("input", function () {
    var raw = clean(input.value);
    // Дефис после четвёртого символа добавляем, пока человек печатает вперёд.
    var next = pretty(raw);
    if (input.value !== next) input.value = next;
    if (msg.hidden === false) say("");
  });

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (busy) return;
    var raw = clean(input.value);
    if (raw.length !== 8) { say(tr("invalid")); input.focus(); return; }
    busy = true;
    submit.disabled = true;
    say("");
    try {
      var r = await fetch("/auth/bot-login/verify", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: pretty(raw) })
      });
      if (r.ok) { location.href = "/app"; return; }
      if (r.status >= 500) say(tr("network"));
      else say(tr("invalid"));
    } catch (err) {
      say(tr("network"));
    }
    busy = false;
    submit.disabled = false;
    input.focus();
  });
})();
