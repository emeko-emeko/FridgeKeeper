(function () {
  document.documentElement.classList.remove("no-js");

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // 1. Появление блоков при прокрутке
  const revealTargets = document.querySelectorAll(
    ".section .card, .section__title, .section__lead, .eyebrow, .hero__title, .hero__sub, .hero__actions, .fridge"
  );
  revealTargets.forEach((el, i) => {
    el.classList.add("reveal");
    el.style.setProperty("--reveal-delay", (i % 3) * 0.08 + "s");
  });

  if ("IntersectionObserver" in window && !reduceMotion) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 }
    );
    revealTargets.forEach((el) => io.observe(el));
  } else {
    revealTargets.forEach((el) => el.classList.add("is-visible"));
  }

  // Подсветка ключевого слова, которая включается вместе с заголовком
  const hl = document.querySelector(".hl");
  if (hl) {
    const parent = hl.closest(".hero__title");
    if (parent) {
      requestAnimationFrame(() => setTimeout(() => parent.classList.add("is-visible"), 300));
    }
  }
    // 7. Шапка: тень при прокрутке
  const nav = document.querySelector(".nav");
  if (nav) {
    const onScroll = () => nav.classList.toggle("is-scrolled", window.scrollY > 8);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // 8. Проблемы <-> этикетка: подсветка связанных элементов
  const label = document.querySelector(".milk-label");
  if (label) {
    const items = document.querySelectorAll(".problem-list li");
    const rows = label.querySelectorAll("[data-spot-target]");
    const setSpot = (n) => {
      label.dataset.active = n;
      items.forEach((li) => li.classList.toggle("is-hot", li.dataset.spot === n));
      rows.forEach((r) => r.classList.toggle("is-hot", r.dataset.spotTarget === n));
    };
    items.forEach((li) => li.addEventListener("pointerenter", () => setSpot(li.dataset.spot)));
    rows.forEach((r) => r.addEventListener("pointerenter", () => setSpot(r.dataset.spotTarget)));
    setSpot("1");
  }

  // 9. Мини-холодильник: клик по зоне показывает инструкцию
  const zones = document.querySelectorAll(".mf-zone");
  const panels = document.querySelectorAll(".step-panel");
  if (zones.length) {
    const showStep = (n) => {
      zones.forEach((z) => z.setAttribute("aria-pressed", String(z.dataset.step === n)));
      panels.forEach((p) => p.classList.toggle("is-active", p.dataset.panel === n));
    };
    zones.forEach((z) => z.addEventListener("click", () => showStep(z.dataset.step)));
  }

  if (reduceMotion) return;

  // 2. Свечение hero за курсором
  const hero = document.querySelector(".hero");
  if (hero) {
    hero.addEventListener("pointermove", (e) => {
      const r = hero.getBoundingClientRect();
      hero.style.setProperty("--mx", e.clientX - r.left + "px");
      hero.style.setProperty("--my", e.clientY - r.top + "px");
    });
  }

  // 3. Свечение внутри карточек
  document.querySelectorAll(".card").forEach((card) => {
    card.addEventListener("pointermove", (e) => {
      const r = card.getBoundingClientRect();
      card.style.setProperty("--cx", e.clientX - r.left + "px");
      card.style.setProperty("--cy", e.clientY - r.top + "px");
    });
  });

  // 4. «Магнитные» кнопки: лёгкое притяжение к курсору
  document.querySelectorAll(".btn").forEach((btn) => {
    btn.addEventListener("pointermove", (e) => {
      const r = btn.getBoundingClientRect();
      const x = (e.clientX - r.left - r.width / 2) * 0.15;
      const y = (e.clientY - r.top - r.height / 2) * 0.25;
      btn.style.setProperty("--btn-x", x + "px");
      btn.style.setProperty("--btn-y", y + "px");
    });
    btn.addEventListener("pointerleave", () => {
      btn.style.setProperty("--btn-x", "0px");
      btn.style.setProperty("--btn-y", "0px");
    });
  });
})();

  // 5. Свечение кнопок за курсором (позиция для --bx / --by)
  document.querySelectorAll(".btn").forEach((btn) => {
    btn.addEventListener("pointermove", (e) => {
      const r = btn.getBoundingClientRect();
      btn.style.setProperty("--bx", e.clientX - r.left + "px");
      btn.style.setProperty("--by", e.clientY - r.top + "px");
    });
  });

  // 6. Список фич: подсветка активного пункта
  const featureItems = document.querySelectorAll(".feature-item");
  if (featureItems.length) {
    const activate = (item) => {
      featureItems.forEach((el) => el.classList.toggle("is-active", el === item));
    };
    activate(featureItems[0]);

    featureItems.forEach((item) => {
      item.addEventListener("pointerenter", () => activate(item));
    });

    // На мобильных и при прокрутке: активен пункт, ближайший к центру экрана
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) activate(entry.target);
          });
        },
        { rootMargin: "-45% 0px -45% 0px" }
      );
      featureItems.forEach((el) => io.observe(el));
    }
  }