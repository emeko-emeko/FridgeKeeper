/* Вход через бота: сайт получает код, пользователь нажимает /start в боте, сайт опрашивает статус.
   Cookie ставит сервер, мы только переходим на /app. */
(function () {
  "use strict";

  var T = {};
  try { T = JSON.parse(document.getElementById("i18n").textContent); } catch (e) {}
  function tr(key) { return T["js_login_" + key] || key; }

  var POLL_MS = 2000;
  var LIMIT_MS = 5 * 60 * 1000;

  var btn = document.getElementById("bot-login");
  var wait = document.getElementById("bot-wait");
  var open = document.getElementById("bot-open");
  var msg = document.getElementById("login-msg");
  var label = btn.querySelector("span");
  var idleLabel = label.textContent;
  var timer = null;
  var stopped = false;

  function say(text, isError) {
    msg.hidden = !text;
    msg.textContent = text || "";
    msg.classList.toggle("is-error", !!isError);
  }

  function stopPolling() {
    stopped = true;
    if (timer) { clearTimeout(timer); timer = null; }
  }

  function reset(text, isError) {
    stopPolling();
    wait.hidden = true;
    btn.disabled = false;
    label.textContent = text ? tr("retry") : idleLabel;
    say(text, isError);
  }

  function poll(code, startedAt) {
    if (stopped) return;
    if (Date.now() - startedAt > LIMIT_MS) { reset(tr("expired"), true); return; }
    timer = setTimeout(async function () {
      if (stopped) return;
      var status = null;
      try {
        var r = await fetch("/auth/bot-login/status?code=" + encodeURIComponent(code), { credentials: "same-origin" });
        if (r.ok) status = (await r.json()).status;
        else if (r.status === 404 || r.status === 410) status = "expired";
      } catch (e) { /* сеть моргнула: пробуем снова до истечения времени */ }
      if (stopped) return;
      if (status === "ok") { stopPolling(); location.href = "/app"; return; }
      if (status === "expired") { reset(tr("expired"), true); return; }
      poll(code, startedAt);
    }, POLL_MS);
  }

  btn.addEventListener("click", async function () {
    if (btn.disabled) return;
    btn.disabled = true;
    say("");
    stopped = false;
    // Окно открываем сразу в обработчике клика: после запроса браузер блокирует всплывающие окна.
    var win = null;
    try { win = window.open("", "_blank"); if (win) win.opener = null; } catch (e) {}
    try {
      var r = await fetch("/auth/bot-login/start", { method: "POST", credentials: "same-origin" });
      if (!r.ok) throw new Error(String(r.status));
      var data = await r.json();
      if (!data.code || !data.bot_url) throw new Error("bad response");
      open.href = data.bot_url;
      wait.hidden = false;
      label.textContent = tr("waiting");
      if (win) win.location.href = data.bot_url;
      poll(data.code, Date.now());
    } catch (e) {
      if (win) win.close();
      reset(tr("error"), true);
    }
  });

  window.addEventListener("pagehide", stopPolling);
})();
