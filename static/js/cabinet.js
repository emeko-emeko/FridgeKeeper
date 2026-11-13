/* Кабинет: числа и график за 14 дней по продуктам из GET /products.
   Дни считаются по Asia/Almaty (UTC+5, без летнего времени). Названия не выводятся. */
(function () {
  "use strict";

  var T = {};
  try { T = JSON.parse(document.getElementById("i18n").textContent); } catch (e) {}
  function tr(key, vars) {
    var s = T["js_cabinet_" + key] || key;
    Object.keys(vars || {}).forEach(function (k) { s = s.split("{" + k + "}").join(vars[k]); });
    return s;
  }

  var $ = function (id) { return document.getElementById(id); };
  var notice = $("notice");
  var DAY = 24 * 3600 * 1000, OFFSET = 5 * 3600 * 1000, DAYS = 14;

  function say(text, isError) {
    notice.textContent = text || "";
    notice.classList.toggle("is-error", !!isError);
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  // Ключ дня YYYY-MM-DD по Almaty из момента времени (мс).
  function dayKey(ms) { return new Date(ms + OFFSET).toISOString().slice(0, 10); }

  function usedDay(iso) {
    if (!iso) return "";
    var s = /[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + "Z";
    var t = Date.parse(s);
    return isNaN(t) ? "" : dayKey(t);
  }

  // День истечения: день после даты срока (дедлайн 00:00 следующего дня).
  function expireDay(iso) {
    if (!iso) return "";
    var p = iso.split("-").map(Number);
    return new Date(Date.UTC(p[0], p[1] - 1, p[2] + 1)).toISOString().slice(0, 10);
  }

  function short(key) { var p = key.split("-"); return p[2] + "." + p[1]; }

  function pct(n, total) { return total ? Math.round((n * 100) / total) : 0; }

  async function load() {
    var r;
    try {
      r = await fetch("/products", { credentials: "same-origin" });
    } catch (e) { say(tr("network"), true); return; }
    if (r.status === 401) {
      say(tr("session_ended"), true);
      setTimeout(function () { location.href = "/login"; }, 1200);
      return;
    }
    if (!r.ok) { say(tr("error", { code: r.status }), true); return; }
    var items;
    try { items = await r.json(); } catch (e) { say(tr("network"), true); return; }
    render(items);
    say("");
  }

  function render(items) {
    var today = dayKey(Date.now());
    var total = items.length, used = 0, expired = 0;
    var days = [], byDay = {};
    for (var i = DAYS - 1; i >= 0; i--) {
      var k = dayKey(Date.now() - i * DAY);
      days.push(k);
      byDay[k] = { used: 0, expired: 0 };
    }
    items.forEach(function (p) {
      if (p.used_at) {
        used++;
        var u = usedDay(p.used_at);
        if (byDay[u]) byDay[u].used++;
      } else if (p.expiry_date) {
        var e = expireDay(p.expiry_date);
        if (e && e <= today) {
          expired++;
          if (byDay[e]) byDay[e].expired++;
        }
      }
    });

    $("cab-used-num").textContent = String(used);
    $("cab-expired-num").textContent = String(expired);
    $("cab-used-pct").textContent = total ? tr("used_pct", { n: pct(used, total) }) : tr("no_products");
    $("cab-expired-pct").textContent = total ? tr("expired_pct", { n: pct(expired, total) }) : tr("no_products");

    var max = 0;
    days.forEach(function (k) { max = Math.max(max, byDay[k].used, byDay[k].expired); });

    var chart = $("cab-chart"), tbody = $("cab-table").querySelector("tbody");
    chart.textContent = "";
    tbody.textContent = "";
    $("cab-empty").hidden = max > 0;
    chart.hidden = max === 0;
    $("cab-table").hidden = max === 0;

    if (max > 0) {
      days.forEach(function (k) {
        var d = byDay[k];
        var col = el("div", "cab-col" + (k === today ? " is-today" : ""));
        var pair = el("div", "cab-pair");
        var bu = el("div", "cab-bar cab-bar--used");
        bu.style.height = (d.used / max * 100) + "%";
        var be = el("div", "cab-bar cab-bar--expired");
        be.style.height = (d.expired / max * 100) + "%";
        if (!d.used) bu.classList.add("cab-bar--none");
        if (!d.expired) be.classList.add("cab-bar--none");
        pair.title = tr("col", { date: short(k), used: d.used, expired: d.expired });
        pair.appendChild(bu);
        pair.appendChild(be);
        col.appendChild(pair);
        col.appendChild(el("span", "cab-day", k.split("-")[2]));
        chart.appendChild(col);

        var row = el("tr");
        row.appendChild(el("th", null, short(k)));
        row.firstChild.scope = "row";
        row.appendChild(el("td", null, String(d.used)));
        row.appendChild(el("td", null, String(d.expired)));
        tbody.appendChild(row);
      });
    }
    $("cab-main").hidden = false;
  }

  say(tr("loading"));
  load();
})();
