(function () {
  document.documentElement.classList.add("js");

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  var S = {};
  try {
    var raw = document.getElementById("i18n");
    S = raw ? JSON.parse(raw.textContent) : {};
  } catch (e) { S = {}; }
  function fmt(template, n) { return (template || "").replace("{n}", n); }

  // 1. Шапка и полоска прогресса
  var nav = document.querySelector(".nav");
  var bar = document.querySelector(".progress__bar");
  function onScroll() {
    if (nav) nav.classList.toggle("is-scrolled", window.scrollY > 8);
    if (bar) {
      var max = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.transform = "scaleX(" + (max > 0 ? window.scrollY / max : 0) + ")";
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // 2. Появление блоков при прокрутке
  var revealEls = document.querySelectorAll(".reveal, .bubble");
  if ("IntersectionObserver" in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
    var chat = document.querySelector(".chat");
    if (chat) {
      var chatIo = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { chat.classList.add("is-visible"); chatIo.disconnect(); }
        });
      }, { threshold: 0.3 });
      chatIo.observe(chat);
    }
  } else {
    revealEls.forEach(function (el) { el.classList.add("is-visible"); });
  }

    // 4. Холодильник: двери открываются по клику, восклицательный знак у скоро испортящегося
  var fridge = document.querySelector("[data-fridge]");
  var infoLine = document.querySelector("[data-info-line]");
  var doors = document.querySelectorAll(".fridge .door");
  var prods = document.querySelectorAll(".fridge .prod");

  function setOpen(open) {
    if (!fridge) return;
    fridge.classList.toggle("is-open", open);
    doors.forEach(function (d) { d.setAttribute("aria-expanded", String(open)); });
  }

  if (fridge) {
    // Клик по любой дверце открывает и закрывает обе
    doors.forEach(function (d) {
      d.addEventListener("click", function () {
        setOpen(!fridge.classList.contains("is-open"));
      });
    });
  }

  prods.forEach(function (p) {
    p.addEventListener("click", function () {
      prods.forEach(function (b) { b.setAttribute("aria-pressed", String(b === p)); });
      if (infoLine) infoLine.textContent = p.getAttribute("data-info") || "";
    });
  });

    // 4. Холодильник: клик по пустому месту закрывает, клик по продукту показывает подпись
  var fridge = document.querySelector("[data-fridge]");
  var infoLine = document.querySelector("[data-info-line]");
  var prods = document.querySelectorAll(".fridge .prod");

  function setOpen(open) {
    if (!fridge) return;
    fridge.classList.toggle("is-open", open);
    fridge.setAttribute("aria-expanded", String(open));
  }

  function showInfo(p) {
    prods.forEach(function (b) { b.setAttribute("aria-pressed", String(b === p)); });
    if (infoLine) infoLine.textContent = p.getAttribute("data-hint") || "";
  }

  if (fridge) {
    fridge.addEventListener("click", function (e) {
      var isOpen = fridge.classList.contains("is-open");
      var prod = e.target.closest(".prod");
      if (prod && isOpen) {
        showInfo(prod);
        return;
      }
      setOpen(!isOpen);
    });

    fridge.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        setOpen(!fridge.classList.contains("is-open"));
      }
    });
  }
  
  // 5. Тема
  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var root = document.documentElement;
      var explicit = root.getAttribute("data-theme");
      var isDark = explicit === "dark" || (!explicit && matchMedia("(prefers-color-scheme: dark)").matches);
      var next = isDark ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("fk-theme", next); } catch (e) {}
    });
  }

  // 6. Вкладки «Всё связано»
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