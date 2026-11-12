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
  var photo = $("photo"), photoBtn = $("photo-btn");
  var review = $("review"), reviewName = $("review-name"), reviewDate = $("review-date");
  var reviewWarn = $("review-warn"), reviewHint = $("review-hint");
  var reviewYes = $("review-yes"), reviewNo = $("review-no");
  var suggested = { name: "", expiry: null };

  // Подписи полей берём из разметки, чтобы не дублировать тексты.
  var LABEL_NAME = $("add-name").parentNode.firstElementChild.textContent;
  var LABEL_DATE = $("add-date").parentNode.firstElementChild.textContent;

  reviewYes.textContent = tr("scan_yes");
  reviewNo.textContent = tr("scan_no");

  function say(text, isError) {
    notice.textContent = text || "";
    notice.classList.toggle("is-error", !!isError);
  }

  async function api(path, options) {
    var r;
    try {
      r = await fetch(path, Object.assign({ credentials: "same-origin" }, options || {}));
    } catch (e) {
      say(tr("network"), true);
      throw e;
    }
    if (r.status === 401) {
      say(tr("session_ended"), true);
      setTimeout(function () { location.href = "/login"; }, 1200);
      throw new Error("401");
    }
    return r;
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
    b.addEventListener("click", handler);
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

    var main = el("div", "app-item__main");
    main.appendChild(el("p", "app-item__name", p.name));
    var meta = d.text + (p.expiry_date ? " · " + tr("until", { date: formatDate(p.expiry_date) }) : "");
    main.appendChild(el("p", "app-item__meta", meta));
    li.appendChild(main);

    var buttons = el("div", "app-item__buttons");
    buttons.appendChild(button(tr("edit"), "app-link", function () { startEdit(li, p); }));
    buttons.appendChild(button(tr("delete"), "app-link app-link--danger", function () { remove(p); }));
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
    box.appendChild(button(tr("save"), "btn btn--primary btn--small", async function () {
      var value = name.value.trim();
      if (!value) { say(tr("name_required"), true); name.focus(); return; }
      var r = await api("/products/" + p.id, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: value, expiry_date: date.value || null, expiry_source: "manual" }),
      });
      if (!r.ok) { say(tr("error", { code: r.status }), true); return; }
      say("");
      load();
    }));
    box.appendChild(button(tr("cancel"), "btn btn--ghost btn--small", load));
    li.appendChild(box);
    name.focus();
  }

  async function remove(p) {
    if (!window.confirm(tr("confirm_delete", { name: p.name }))) return;
    var r = await api("/products/" + p.id, { method: "DELETE" });
    if (!r.ok) { say(tr("error", { code: r.status }), true); return; }
    say("");
    load();
  }

  function sortKey(p) {
    return p.expiry_date ? deadlineMs(p.expiry_date) : Infinity;
  }

  async function load() {
    var r;
    try { r = await api("/products"); } catch (e) { return; }
    if (!r.ok) { say(tr("error", { code: r.status }), true); return; }
    var items = await r.json();
    items.sort(function (a, b) { return sortKey(a) - sortKey(b); });
    list.textContent = "";
    items.forEach(function (p) { list.appendChild(renderItem(p)); });
    empty.textContent = items.length ? "" : tr("empty");
  }

  // Добавление вручную
  $("add-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    var name = $("add-name").value.trim();
    if (!name) { say(tr("name_required"), true); return; }
    var r = await api("/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name, expiry_date: $("add-date").value || null, expiry_source: "manual" }),
    });
    if (!r.ok) { say(tr("error", { code: r.status }), true); return; }
    say(tr("saved", { name: name }));
    $("add-form").reset();
    load();
  });

  // Фото
  function resetReview() {
    review.hidden = true;
    reviewWarn.hidden = true;
    reviewHint.textContent = "";
    reviewName.value = "";
    reviewDate.value = "";
    suggested = { name: "", expiry: null };
    photo.value = "";
  }

  photoBtn.addEventListener("click", function () { photo.click(); });

  photo.addEventListener("change", async function () {
    var file = photo.files && photo.files[0];
    if (!file) return;
    resetReview();
    say(tr("scanning"));
    photoBtn.disabled = true;
    var form = new FormData();
    form.append("file", file);
    try {
      var r = await api("/products/scan", { method: "POST", body: form });
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
    } catch (err) {
      /* сообщение уже показано в api() */
    } finally {
      photoBtn.disabled = false;
    }
  });

  review.addEventListener("submit", async function (e) {
    e.preventDefault();
    var name = reviewName.value.trim();
    if (!name) { reviewHint.textContent = tr("name_required"); return; }
    // Источник «ocr», только если пользователь не менял предложенные значения.
    var unchanged = name === suggested.name && (reviewDate.value || null) === suggested.expiry;
    var r = await api("/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name, expiry_date: reviewDate.value || null, expiry_source: unchanged ? "ocr" : "manual" }),
    });
    if (!r.ok) { say(tr("error", { code: r.status }), true); return; }
    resetReview();
    say(tr("saved", { name: name }));
    load();
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

  say(tr("loading"));
  load().then(function () { if (notice.textContent === tr("loading")) say(""); });
})();
