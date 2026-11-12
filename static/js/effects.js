(function () {
  document.documentElement.classList.add("js");
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var fine = matchMedia("(hover: hover) and (pointer: fine)").matches;
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }

  // 1. Шапка и прогресс
  var nav = $(".nav"), bar = $(".progress__bar");
  function onScroll() {
    if (nav) nav.classList.toggle("is-scrolled", window.scrollY > 8);
    if (bar) {
      var max = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.transform = "scaleX(" + (max > 0 ? window.scrollY / max : 0) + ")";
    }
  }
  addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // 2. Появление при прокрутке (чат проигрывается заново по клику)
  var chat = $("[data-chat]");
  if ("IntersectionObserver" in window && !reduce) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("is-visible"); io.unobserve(e.target); }
      });
    }, { threshold: 0.15 });
    $$(".reveal").forEach(function (el) { io.observe(el); });
  } else {
    $$(".reveal").forEach(function (el) { el.classList.add("is-visible"); });
  }
  if (chat) {
    chat.addEventListener("click", function () {
      chat.classList.remove("is-visible");
      void chat.offsetWidth;
      chat.classList.add("is-visible");
    });
  }

  // 3. Холодильник: один обработчик на дверцы, один на внутренность
  var fridge = $("[data-fridge]");
  if (fridge) {
    var doors = $$(".door", fridge), prods = $$(".prod", fridge);
    var line = $("[data-info-line]"), meter = $("[data-meter]");
    var def = line ? line.textContent : "";

    function setMeter(v) {
      if (!meter) return;
      meter.parentNode.style.opacity = v === null ? "0" : "1";
      if (v === null) return;
      meter.style.setProperty("--w", v + "%");
      meter.style.setProperty("--c", v <= 25 ? "var(--accent)" : v <= 55 ? "var(--orange)" : "var(--green)");
    }
    function reset() {
      prods.forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
      if (line) line.textContent = def;
      setMeter(null);
    }
    function setOpen(open) {
      fridge.classList.toggle("is-open", open);
      doors.forEach(function (d) { d.setAttribute("aria-expanded", String(open)); });
      if (!open) reset();
    }
    reset();

    doors.forEach(function (d) {
      d.addEventListener("click", function () { setOpen(!fridge.classList.contains("is-open")); });
    });
    $(".fridge__inside", fridge).addEventListener("click", function (e) {
      var p = e.target.closest(".prod");
      if (!p) { setOpen(false); return; }
      prods.forEach(function (b) { b.setAttribute("aria-pressed", String(b === p)); });
      if (line) line.textContent = p.getAttribute("data-hint") || "";
      setMeter(parseInt(p.getAttribute("data-fresh"), 10) || 0);
    });
    addEventListener("keydown", function (e) {
      if (e.key === "Escape" && fridge.classList.contains("is-open")) setOpen(false);
    });
  }

  // 4. Тема
  var toggle = $(".theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var root = document.documentElement, ex = root.getAttribute("data-theme");
      var dark = ex === "dark" || (!ex && matchMedia("(prefers-color-scheme: dark)").matches);
      var next = dark ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("fk-theme", next); } catch (e) {}
    });
  }

  // 5. Вкладки «Всё связано»
  var feats = $$(".feature"), panels = $$(".preview__panel");
  function showFeature(n) {
    feats.forEach(function (li) {
      var on = li.getAttribute("data-feature") === n;
      li.classList.toggle("is-active", on);
      li.setAttribute("aria-selected", on ? "true" : "false");
    });
    panels.forEach(function (p) { p.classList.toggle("is-on", p.getAttribute("data-fp") === n); });
  }
  feats.forEach(function (li) {
    var n = li.getAttribute("data-feature");
    li.addEventListener("click", function () { showFeature(n); });
    li.addEventListener("mouseenter", function () { if (fine) showFeature(n); });
    li.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); showFeature(n); }
    });
  });

  // 6. Наклон блоков и свет под курсором
  if (fine && !reduce) {
    $$(".tilt").forEach(function (el) {
      el.addEventListener("pointermove", function (e) {
        var r = el.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
        el.classList.add("is-tilting");
        el.style.setProperty("--gx", x * 100 + "%");
        el.style.setProperty("--gy", y * 100 + "%");
        el.style.transform = "perspective(900px) rotateX(" + ((0.5 - y) * 5) + "deg) rotateY(" + ((x - 0.5) * 6) + "deg) translateY(-3px)";
      });
      el.addEventListener("pointerleave", function () {
        el.classList.remove("is-tilting");
        el.style.transform = "";
      });
    });
    $$(".btn").forEach(function (b) {
      b.addEventListener("pointermove", function (e) {
        var r = b.getBoundingClientRect();
        b.style.setProperty("--mx", e.clientX - r.left + "px");
        b.style.setProperty("--my", e.clientY - r.top + "px");
      });
    });
  }
})();