/* Веб-интерфейс /app: список продуктов, добавление, правка, удаление, распознавание фото.
   Вход по cookie fk_session, запросы идут на тот же домен. Названия вставляются через
   textContent, поэтому введённый текст не выполняется как HTML. */
(function () {
  "use strict";

  var T = {};
  try { T = JSON.parse(document.getElementById("i18n").textContent); } catch (e) {}
  function tr(key, vars) {
    var s = T["js_app_" + key] || key;
    Object.keys(vars || {}).forEach(function (k) { s = s.split("{" + k + "}").join(vars[k]); });
    return s;
  }

  var $ = function (id) { return document.getElementById(id); };
  var notice = $("notice"), list = $("list"), empty = $("empty");
  var gate = $("gate"), main = $("main"), gateCheck = $("gate-check");
  var review = $("review"), reviewName = $("review-name"), reviewDate = $("review-date");
  var reviewWarn = $("review-warn"), reviewHint = $("review-hint");
  var reviewYes = $("review-yes"), reviewNo = $("review-no");
  var addForm = $("add-form"), addSubmit = $("add-submit");
  var photoInputs = [$("photo-camera"), $("photo-file")];
  var photoButtons = [$("photo-camera-btn"), $("photo-file-btn")];
  var suggested = { name: "", expiry: null };
  var summary = $("summary"), DEFAULT_TITLE = summary.textContent;
  var headAdd = $("head-add");
  headAdd.addEventListener("click", function () {
    $("add-name").scrollIntoView({ block: "center" });
    $("add-name").focus();
  });
  $("empty-photo").addEventListener("click", function () { photoInputs[0].click(); });

  // Подписи полей берём из разметки, чтобы не дублировать тексты.
  var LABEL_NAME = $("add-name").parentNode.firstElementChild.textContent;
  var LABEL_DATE = $("add-date").parentNode.firstElementChild.textContent;

  reviewYes.textContent = tr("scan_yes");
  reviewNo.textContent = tr("scan_no");

  function say(text, isError) {
    notice.textContent = text || "";
    notice.classList.toggle("is-error", !!isError);
  }

  // Запрос. Сетевая ошибка и 401 показываются здесь же; такие исключения помечены handled.
  async function api(path, options) {
    var r;
    try {
      r = await fetch(path, Object.assign({ credentials: "same-origin" }, options || {}));
    } catch (e) {
      say(tr("network"), true);
      e.handled = true;
      throw e;
    }
    if (r.status === 401) {
      say(tr("session_ended"), true);
      setTimeout(function () { location.href = "/login"; }, 1200);
      var err = new Error("401");
      err.handled = true;
      throw err;
    }
    return r;
  }

  // Выполняет действие, пока нужные кнопки заблокированы. Любая ошибка даёт сообщение, а не тихое молчание.
  async function locked(buttons, action) {
    buttons.forEach(function (b) { if (b) b.disabled = true; });
    try {
      await action();
    } catch (e) {
      if (!e || !e.handled) say(tr("network"), true);
    } finally {
      buttons.forEach(function (b) { if (b) b.disabled = false; });
    }
  }

  // Срок: дедлайн в 00:00 следующего дня по Asia/Almaty (UTC+5, без перехода на летнее время).
  function deadlineMs(iso) {
    var p = iso.split("-").map(Number);
    return Date.UTC(p[0], p[1] - 1, p[2] + 1) - 5 * 3600 * 1000;
  }

  function describe(iso) {
    if (!iso) return { level: "none", text: tr("no_date") };
    var HOUR = 3600 * 1000;
    var diff = deadlineMs(iso) - Date.now();
    if (diff <= 0) {
      var ago = Math.max(1, Math.floor(-diff / HOUR));
      return {
        level: "expired",
        text: ago < 48 ? tr("expired_hours", { n: ago }) : tr("expired_days", { n: Math.floor(ago / 24) }),
      };
    }
    var hours = Math.max(1, Math.ceil(diff / HOUR));
    var level = hours <= 24 ? "urgent" : hours <= 72 ? "soon" : "ok";
    return {
      level: level,
      text: hours < 48 ? tr("left_hours", { n: hours }) : tr("left_days", { n: Math.ceil(hours / 24) }),
    };
  }

  function formatDate(iso) {
    var p = iso.split("-");
    return p[2] + "." + p[1] + "." + p[0];
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function button(label, cls, handler) {
    var b = el("button", cls, label);
    b.type = "button";
    b.addEventListener("click", function () { handler(b); });
    return b;
  }

  function field(label, input, grow) {
    var l = el("label", "app-field" + (grow ? " app-field--grow" : ""));
    l.appendChild(el("span", null, label));
    l.appendChild(input);
    return l;
  }

  function renderItem(p) {
    var d = describe(p.expiry_date);
    var li = el("li", "app-item app-item--" + d.level);

    var body = el("div", "app-item__main");
    body.appendChild(el("p", "app-item__name", p.name));
    if (p.expiry_date) body.appendChild(el("p", "app-item__meta", tr("until", { date: formatDate(p.expiry_date) })));
    li.appendChild(body);
    li.appendChild(el("span", "app-pill app-pill--" + d.level, d.text));

    var buttons = el("div", "app-item__buttons");
    buttons.appendChild(button(tr("edit"), "app-link", function () { startEdit(li, p); }));
    buttons.appendChild(button(tr("delete"), "app-link app-link--danger", function (b) { remove(p, b); }));
    li.appendChild(buttons);
    return li;
  }

  function startEdit(li, p) {
    li.textContent = "";
    var name = el("input");
    name.type = "text"; name.maxLength = 100; name.value = p.name;
    var date = el("input");
    date.type = "date"; date.value = p.expiry_date || "";

    var box = el("div", "app-item__edit");
    box.appendChild(field(LABEL_NAME, name, true));
    box.appendChild(field(LABEL_DATE, date, false));
    var actions = el("div", "app-item__edit-actions");
    var cancel = button(tr("cancel"), "btn btn--ghost btn--small", function () { load(); });
    var save = button(tr("save"), "btn btn--primary btn--small", function () {
      var value = name.value.trim();
      if (!value) { say(tr("name_required"), true); name.focus(); return; }
      locked([save, cancel], async function () {
        var r = await api("/products/" + p.id, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: value, expiry_date: date.value || null, expiry_source: "manual" }),
        });
        if (!r.ok) { say(tr("error", { code: r.status }), true); return; }
        say("");
        await load();
      });
    });
    actions.appendChild(save);
    actions.appendChild(cancel);
    box.appendChild(actions);
    li.appendChild(box);
    name.focus();
  }

  function remove(p, btn) {
    if (!window.confirm(tr("confirm_delete", { name: p.name }))) return;
    var siblings = btn && btn.parentNode ? Array.prototype.slice.call(btn.parentNode.children) : [btn];
    return locked(siblings, async function () {
      var r = await api("/products/" + p.id, { method: "DELETE" });
      if (!r.ok) { say(tr("error", { code: r.status }), true); return; }
      say("");
      await load();
    });
  }

  function sortKey(p) {
    return p.expiry_date ? deadlineMs(p.expiry_date) : Infinity;
  }

  async function load() {
    var r;
    try { r = await api("/products"); } catch (e) { if (!e.handled) say(tr("network"), true); return; }
    if (!r.ok) { say(tr("error", { code: r.status }), true); return; }
    var items;
    try { items = await r.json(); } catch (e) { say(tr("network"), true); return; }
    items.sort(function (a, b) { return sortKey(a) - sortKey(b); });
    list.textContent = "";
    var order = ["expired", "urgent", "soon", "ok", "none"];
    var names = { expired: "g_expired", urgent: "g_today", soon: "g_soon", ok: "g_later", none: "g_none" };
    var groups = {};
    order.forEach(function (k) { groups[k] = []; });
    items.forEach(function (p) { groups[describe(p.expiry_date).level].push(p); });
    order.forEach(function (k) {
      if (!groups[k].length) return;
      var sec = el("section", "app-group app-group--" + k);
      var h = el("h3", "app-group__title", tr(names[k]));
      h.appendChild(el("span", "app-group__count", String(groups[k].length)));
      sec.appendChild(h);
      var ul = el("ul", "app-list");
      groups[k].forEach(function (p) { ul.appendChild(renderItem(p)); });
      sec.appendChild(ul);
      list.appendChild(sec);
    });
    empty.hidden = items.length > 0;
    summary.textContent = summaryText(groups, items.length);
  }

  function summaryText(g, total) {
    var soon = g.urgent.length + g.soon.length;
    if (soon) return tr("sum_soon", { n: soon });
    if (g.expired.length) return tr("sum_expired", { n: g.expired.length });
    return total ? tr("sum_ok") : DEFAULT_TITLE;
  }

  // Добавление вручную
  addForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var name = $("add-name").value.trim();
    if (!name) { say(tr("name_required"), true); return; }
    locked([addSubmit], async function () {
      var r = await api("/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name, expiry_date: $("add-date").value || null, expiry_source: "manual" }),
      });
      if (!r.ok) { say(tr("error", { code: r.status }), true); return; }
      say(tr("saved", { name: name }));
      addForm.reset();
      await load();
    });
  });

  // Фото: две кнопки (камера и файл) ведут в один обработчик
  function resetReview() {
    review.hidden = true;
    reviewWarn.hidden = true;
    reviewHint.textContent = "";
    reviewName.value = "";
    reviewDate.value = "";
    suggested = { name: "", expiry: null };
    photoInputs.forEach(function (i) { i.value = ""; });
  }

  photoButtons[0].addEventListener("click", function () { photoInputs[0].click(); });
  photoButtons[1].addEventListener("click", function () { photoInputs[1].click(); });

  // Уменьшаем фото в браузере: Vercel не принимает тела больше ~4,5 МБ (413).
  // Если браузер не смог прочитать файл, отправляем оригинал.
  async function shrinkPhoto(file) {
    try {
      var bmp = await createImageBitmap(file);
      var scale = Math.min(1, 1600 / Math.max(bmp.width, bmp.height));
      var canvas = document.createElement("canvas");
      canvas.width = Math.round(bmp.width * scale);
      canvas.height = Math.round(bmp.height * scale);
      canvas.getContext("2d").drawImage(bmp, 0, 0, canvas.width, canvas.height);
      var blob = await new Promise(function (resolve) { canvas.toBlob(resolve, "image/jpeg", 0.8); });
      return blob || file;
    } catch (e) {
      return file;
    }
  }

  function handlePhoto(input) {
    var file = input.files && input.files[0];
    if (!file) return;
    resetReview();
    say(tr("scanning"));
    locked(photoButtons, async function () {
      var blob = await shrinkPhoto(file);
      var form = new FormData();
      form.append("file", blob, "label.jpg");
      var r = await api("/products/scan", { method: "POST", body: form });
      if (r.status === 413) { say(tr("too_big"), true); return; }
      if (!r.ok) { say(tr("error", { code: r.status }), true); return; }
      var data = await r.json();
      suggested = { name: data.product_name || "", expiry: data.expiry_date };
      reviewName.value = suggested.name;
      reviewDate.value = suggested.expiry || "";
      reviewWarn.textContent = tr("scan_expired");
      reviewWarn.hidden = !data.expired;
      reviewHint.textContent = suggested.name ? tr("scan_ok") : tr("scan_noname");
      review.hidden = false;
      say("");
      reviewName.focus();
    });
  }
  photoInputs.forEach(function (input) {
    input.addEventListener("change", function () { handlePhoto(input); });
  });

  review.addEventListener("submit", function (e) {
    e.preventDefault();
    var name = reviewName.value.trim();
    if (!name) { reviewHint.textContent = tr("name_required"); return; }
    // Источник «ocr», только если пользователь не менял предложенные значения.
    var unchanged = name === suggested.name && (reviewDate.value || null) === suggested.expiry;
    locked([reviewYes, reviewNo], async function () {
      var r = await api("/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name, expiry_date: reviewDate.value || null, expiry_source: unchanged ? "ocr" : "manual" }),
      });
      if (!r.ok) { say(tr("error", { code: r.status }), true); return; }
      resetReview();
      say(tr("saved", { name: name }));
      await load();
    });
  });

  reviewNo.addEventListener("click", function () {
    reviewName.value = "";
    reviewDate.value = "";
    reviewWarn.hidden = true;
    reviewHint.textContent = tr("scan_manual");
    suggested = { name: "", expiry: null };
    reviewName.focus();
  });

  // Выход
  $("logout").addEventListener("click", async function () {
    try { await fetch("/auth/logout", { method: "POST", credentials: "same-origin" }); } catch (e) {}
    location.href = "/login";
  });

  // Блокировка без /start: пока бот не запущен, форму и список не показываем и продукты не запрашиваем.
  // Если поля bot_started в ответе нет вовсе, считаем, что бот запущен.
  async function botStarted() {
    var r = await api("/auth/me");
    if (!r.ok) return true;
    var data = await r.json();
    return data.bot_started !== false;
  }

  function showApp() {
    gate.hidden = true;
    document.getElementById("head-bot").hidden = false;
    main.hidden = false;
    headAdd.hidden = false;
    say(tr("loading"));
    return load().then(function () { if (notice.textContent === tr("loading")) say(""); });
  }

  function showGate() {
    main.hidden = true;
    headAdd.hidden = true;
    document.getElementById("head-bot").hidden = true;
    gate.hidden = false;
    say("");
  }

  gateCheck.addEventListener("click", function () {
    locked([gateCheck], async function () {
      if (await botStarted()) { await showApp(); } else { say(tr("gate_still"), true); }
    });
  });

  say(tr("loading"));
  botStarted().then(function (ok) {
    return ok ? showApp() : showGate();
  }).catch(function (e) {
    // Сеть недоступна: сообщение уже показано в api(). 401 ведёт на /login.
    if (!e || !e.handled) say(tr("network"), true);
  });
})();
