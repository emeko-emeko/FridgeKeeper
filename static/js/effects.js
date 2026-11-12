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

  // 2. Появление при прокрутке. Если загружен GSAP, этим занимается раздел 3
  var useGsap = !!(window.gsap && window.ScrollTrigger);
  if ("IntersectionObserver" in window && !reduce && !useGsap) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("is-visible"); io.unobserve(e.target); }
      });
    }, { threshold: 0.15 });
    $$(".reveal").forEach(function (el) { io.observe(el); });
  } else {
    $$(".reveal").forEach(function (el) { el.classList.add("is-visible"); });
  }

  // 3. Движение первого экрана: GSAP и Lenis (только лендинг, только без reduced-motion)
  var hero = $(".hero");
  if (hero && !reduce && window.gsap && window.ScrollTrigger) {
    gsap.registerPlugin(ScrollTrigger);

    if (window.Lenis) {
      var lenis = new Lenis({ duration: 1.1 });
      lenis.on("scroll", ScrollTrigger.update);
      gsap.ticker.add(function (t) { lenis.raf(t * 1000); });
      gsap.ticker.lagSmoothing(0);
      // Ссылки-якоря шапки едут плавно вместе с Lenis
      $$('a[href^="#"]').forEach(function (a) {
        a.addEventListener("click", function (e) {
          var id = a.getAttribute("href"), target = id.length > 1 ? $(id) : null;
          if (!target) return;
          e.preventDefault();
          lenis.scrollTo(target, { offset: -72 });
        });
      });
    }

    // Вход: текст по очереди, фото раскрывается сверху вниз, наклейка прилипает
    var tl = gsap.timeline({ defaults: { ease: "power3.out" } });
    tl.from(".hero .eyebrow", { y: 16, opacity: 0, duration: 0.6 })
      .from(".hero__title", { y: 28, opacity: 0, duration: 0.8 }, "-=0.35")
      .from(".hero__sub", { y: 20, opacity: 0, duration: 0.6 }, "-=0.5")
      .from(".hero .hero__actions > *", { y: 16, opacity: 0, duration: 0.6, stagger: 0.1 }, "-=0.45")
      .from(".window", { y: 56, opacity: 0, duration: 1, ease: "power3.out" }, "-=0.3")
      .from(".hero__phone", { y: 72, opacity: 0, duration: 1, ease: "power3.out" }, "-=0.75")
      .from(".hero__tag", { y: 28, opacity: 0, rotate: -7, duration: 0.7, ease: "power3.out" }, "-=0.5")
      .from(".hero__tag .meter b", { scaleX: 0, duration: 1.2, ease: "power3.out" }, "-=0.3");

    // Секции: каждый блок поднимается и проявляется, когда доходит до нижней трети экрана
    $$(".reveal").forEach(function (el) {
      el.classList.add("is-visible");
      el.style.transition = "none";
      gsap.from(el, {
        y: 20, opacity: 0, duration: 0.5, ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 88%", once: true }
      });
    });

    // Три проблемы: по очереди слева направо
    var issues = $$(".issues li");
    if (issues.length) {
      gsap.set(issues, { y: 20, opacity: 0 });
      ScrollTrigger.batch(issues, {
        start: "top 90%", once: true,
        onEnter: function (items) {
          gsap.to(items, { y: 0, opacity: 1, duration: 0.5, ease: "power3.out", stagger: 0.06 });
        }
      });
    }

    // Блок со скриншотами чуть плывёт вверх, пока его проходишь
    var stage = $(".preview");
    if (stage) {
      gsap.fromTo(stage, { yPercent: 4 }, {
        yPercent: -4, ease: "none",
        scrollTrigger: { trigger: stage, start: "top bottom", end: "bottom top", scrub: true }
      });
    }

    // Фото в секциях: параллакс внутри рамки (запас 8% задан в CSS)
    $$(".photo__img").forEach(function (img) {
      gsap.fromTo(img, { yPercent: 5 }, {
        yPercent: -5, ease: "none",
        scrollTrigger: { trigger: img.parentElement, start: "top bottom", end: "bottom top", scrub: true }
      });
    });

    // Телефон в первом экране чуть обгоняет окно при прокрутке: объём
    gsap.fromTo(".hero__phone", { yPercent: 4 }, {
      yPercent: -12, ease: "none",
      scrollTrigger: { trigger: hero, start: "top top", end: "bottom top", scrub: true }
    });
  }

  // Жёлтая полоса за ключевым словом: один раз при появлении, дальше статична
  $$(".hl--dither").forEach(function (el) {
    if (reduce || !(window.gsap && window.ScrollTrigger)) { el.classList.add("is-marked"); return; }
    ScrollTrigger.create({
      trigger: el, start: "top 90%", once: true,
      onEnter: function () { el.classList.add("is-marked"); }
    });
  });

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
    li.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); showFeature(n); }
    });
  });

})();