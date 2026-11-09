(function () {
  document.documentElement.classList.add("js");

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var S = {};
  try {
    var raw = document.getElementById("i18n");
    S = raw ? JSON.parse(raw.textContent) : {};
  } catch (e) { S = {}; }
  function fmt(template, n) { return (template || "").replace("{n}", n); }

  // 1. Шапка
  var nav = document.querySelector(".nav");
  if (nav) {
    var onNavScroll = function () { nav.classList.toggle("is-scrolled", window.scrollY > 8); };
    window.addEventListener("scroll", onNavScroll, { passive: true });
    onNavScroll();
  }

  // 2. Появление и уход блоков при прокрутке (вверх и вниз)
  var revealEls = document.querySelectorAll(".reveal, .rise, .fridge, .item, .step, .mini__zone, .feature, .preview, .row");
  if ("IntersectionObserver" in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var el = entry.target;
        if (entry.isIntersecting) {
          el.classList.add("is-visible");
          el.classList.remove("is-leaving");
        } else if (el.classList.contains("is-visible")) {
          // уехал вверх или вниз: прячем с направлением
          el.classList.add("is-leaving");
          el.classList.remove("is-visible");
          el.setAttribute("data-dir", entry.boundingClientRect.top < 0 ? "up" : "down");
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("is-visible"); });
  }

  // 3. Холодильник: сроки и подсказка
  var items = document.querySelectorAll(".fridge .item");
  var infoLine = document.querySelector("[data-info-line]");
  var countEl = document.querySelector("[data-count]");
  if (countEl) countEl.textContent = fmt(S.js_count_fmt, items.length);

  function statusFor(days) { return days > 3 ? "ok" : days > 1 ? "soon" : "urgent"; }
  function renderItem(btn, days) {
    var label = btn.querySelector(".item__days");
    btn.classList.remove("item--ok", "item--soon", "item--urgent");
    btn.classList.add("item--" + statusFor(days));
    if (label) label.textContent = days <= 0 ? (S.js_today || "") : fmt(S.js_days_fmt, Math.ceil(days));
  }

  var startDays = [];
  items.forEach(function (btn, i) {
    var d = parseFloat(btn.getAttribute("data-days")) || 0;
    startDays[i] = d;
    renderItem(btn, d);
  });

  if (!reduceMotion && items.length) {
    var currentDays = startDays.slice();
    setInterval(function () {
      var allDone = currentDays.every(function (d) { return d <= 0; });
      currentDays = allDone ? startDays.slice() : currentDays.map(function (d) { return Math.max(0, d - 0.5); });
      items.forEach(function (btn, i) { renderItem(btn, currentDays[i]); });
    }, 3000);
  }

  items.forEach(function (btn) {
    btn.addEventListener("click", function () {
      items.forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      if (infoLine) infoLine.textContent = btn.getAttribute("data-info") || "";
    });
  });

  // 4. Дверца холодильника
  var door = document.querySelector(".fridge__door");
  if (door) {
    door.addEventListener("click", function () {
      var open = door.getAttribute("aria-expanded") === "true";
      door.setAttribute("aria-expanded", String(!open));
    });
  }

  // 5. Тема
  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var root = document.documentElement;
      var explicit = root.getAttribute("data-theme");
      var isDark = explicit === "dark" || (!explicit && matchMedia("(prefers-color-scheme: dark)").matches);
      root.setAttribute("data-theme", isDark ? "light" : "dark");
    });
  }

  // 6. Мини-холодильник: шаги
  var zones = document.querySelectorAll(".mini__zone");
  var panels = document.querySelectorAll(".step");
  if (zones.length) {
    var showStep = function (n) {
      zones.forEach(function (z) { z.setAttribute("aria-pressed", String(z.getAttribute("data-step") === n)); });
      panels.forEach(function (p) { p.classList.toggle("is-active", p.getAttribute("data-panel") === n); });
    };
    zones.forEach(function (z) { z.addEventListener("click", function () { showStep(z.getAttribute("data-step")); }); });
  }

  // 7. Всё связано
  var features = document.querySelectorAll(".feature");
  var fPanels = document.querySelectorAll(".preview__panel");
  if (features.length) {
    var showFeature = function (n) {
      features.forEach(function (li) {
        var on = li.getAttribute("data-feature") === n;
        li.classList.toggle("is-active", on);
        li.setAttribute("aria-selected", on ? "true" : "false");
      });
      fPanels.forEach(function (p) { p.classList.toggle("is-on", p.getAttribute("data-fp") === n); });
    };
    features.forEach(function (li) {
      li.addEventListener("click", function () { showFeature(li.getAttribute("data-feature")); });
      li.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); showFeature(li.getAttribute("data-feature")); }
      });
    });
  }
})();